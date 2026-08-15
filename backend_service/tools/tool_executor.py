"""
Tool Executor that communicates with the Hypernet CRM API.
"""
import os
import requests
import time
from application.monitoring.logger import AppLogger
from application.shared.exceptions.permission_exceptions import (
    PermissionDeniedException,
    AgentEmergencyStopException,
)

logger = AppLogger.get_logger("tool_executor")
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "http://localhost:8090/api/crm")

from application.shared.utils.tracer import trace_all_methods

@trace_all_methods
class ToolExecutor:
    def __init__(self, permission_service=None, crm_client=None):
        self._permission_svc = permission_service
        self._crm_client = crm_client

    def execute(self, tool_name: str, parameters: dict, session_id: str = None):
        # ── LAYER 3: Final hard check before ANY HTTP call ─────────────────
        if self._permission_svc:
            if not self._permission_svc.is_allowed("GLOBAL_AGENT"):
                logger.critical(f"[LAYER 3 BLOCK] GLOBAL_AGENT disabled — '{tool_name}' BLOCKED")
                raise AgentEmergencyStopException()

            if not self._permission_svc.is_allowed("CRM"):
                logger.critical(f"[LAYER 3 BLOCK] CRM service disabled — '{tool_name}' BLOCKED")
                raise PermissionDeniedException(
                    tool_name="CRM",
                    reason="All CRM access has been suspended by an administrator."
                )

            if not self._permission_svc.is_allowed(tool_name):
                logger.warning(f"[LAYER 3 BLOCK] Tool '{tool_name}' BLOCKED")
                raise PermissionDeniedException(
                    tool_name=tool_name,
                    reason=f"The action '{tool_name}' is currently disabled. Please contact support."
                )
        # ──────────────────────────────────────────────────────────────────

        logger.info(f"Executing tool {tool_name} with params {parameters}")
        try:
            customer_id = parameters.get("crm_customer_id") or parameters.get("customer_id")
            
            if tool_name in ("get_customer_info", "get_balance", "get_current_package", "get_available_packages"):
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                    
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                    
                # 1. Fetch from real CRM
                response = self._crm_client.get_user_overview(customer_id)
                
                # 2. Apply business logic transformations to aid the LLM
                if response.get("success") and "data" in response:
                    data = response["data"]
                    notes = []
                    
                    user_profile_type = int(data.get("profile_type"))
                    
                    rx_mb = 0.0
                    if "remaining_rx" in data and data["remaining_rx"] is not None:
                        try:
                            rx_mb = float(data["remaining_rx"])
                        except (ValueError, TypeError):
                            pass
                            
                    is_quota_finished = (user_profile_type == 0 and rx_mb <= 0)
                    
                    # Convert remaining_rx based on user_profile_type
                    if "remaining_rx" in data and data["remaining_rx"] is not None:
                        if user_profile_type == 4 or is_quota_finished:
                            data["remaining_rx"] = "0 MB"
                        else:
                            if rx_mb > 1024:
                                data["remaining_rx"] = f"{rx_mb / 1024:.2f} GB"
                            else:
                                data["remaining_rx"] = f"{rx_mb:.2f} MB"
                            
                    # Advanced Profile and Status Logic
                    profile_id = data.get("profile_id")
                    username = data.get("username")
                    
                    # PARALLEL CRM FETCHING (Sync over threads)
                    import concurrent.futures
                    
                    def fetch_profile():
                        return self._crm_client.get_profile(profile_id) if profile_id else {}
                    def fetch_search():
                        return self._crm_client.search_users(username) if username else {}
                    def fetch_rate():
                        return self._crm_client.get_user_current_rate(customer_id)
                    def fetch_invoices():
                        return self._crm_client.get_user_invoices(customer_id)
                    def fetch_packages():
                        return self._crm_client.get_available_packages(customer_id)
                    def fetch_iptv():
                        iptv_type = data.get("iptv_type")
                        if iptv_type and iptv_type != "none":
                            return self._crm_client.get_iptv_expiration(customer_id)
                        return {}
                        
                    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                        f_profile = executor.submit(fetch_profile)
                        f_search = executor.submit(fetch_search)
                        f_rate = executor.submit(fetch_rate)
                        f_iptv = executor.submit(fetch_iptv)
                        
                        f_invoices = None
                        f_packages = None
                        if tool_name == "get_available_packages" and user_profile_type != 4:
                            f_invoices = executor.submit(fetch_invoices)
                            f_packages = executor.submit(fetch_packages)
                        
                        prof_res = f_profile.result()
                        search_res = f_search.result()
                        rate_res = f_rate.result()
                        iptv_res = f_iptv.result()
                        inv_res = f_invoices.result() if f_invoices else None
                        res_pkg = f_packages.result() if f_packages else None
                    
                    if prof_res and prof_res.get("success") and "data" in prof_res:
                            prof_data = prof_res.get("data", {}).get("data", {})
                            
                            # Add raw profile fields for context
                            data["profile_details"] = prof_data
                            
                            # Format Speeds
                            def fmt_speed(kbps):
                                try:
                                    k = int(kbps)
                                    if k >= 1024: return f"{k // 1024} Mbps"
                                    return f"{k} Kbps"
                                except:
                                    return str(kbps)
                                    
                            uprate = fmt_speed(prof_data.get("uprate", 0))
                            downrate = fmt_speed(prof_data.get("downrate", 0))
                            price = prof_data.get("price", "غير معروف")
                            
                            if user_profile_type == 4:
                                notes.append(f"حقيقة: السرعة الحالية لباقة العميل هي {downrate} تحميل و {uprate} رفع بسعر {price} ل.س.")
                                notes.append("حقيقة: باقة العميل الحالية غير محدودة التحميل (Unlimited Quota).")
                            elif user_profile_type == 0:
                                dl_amt = prof_data.get("download_amount")
                                if dl_amt is not None:
                                    try:
                                        dl_gb = float(dl_amt) / 1024
                                        notes.append(f"حقيقة: الحجم الكلي المخصص لباقة العميل هو {dl_gb:g} GB.")
                                    except:
                                        pass
                                
                                next_prof_id = prof_data.get("quota_next_profile_id")
                                
                                if is_quota_finished:
                                    if next_prof_id:
                                        next_prof_res = self._crm_client.get_profile(next_prof_id)
                                        if next_prof_res.get("success") and "data" in next_prof_res:
                                            n_data = next_prof_res.get("data", {}).get("data", {})
                                            n_uprate = fmt_speed(n_data.get("uprate", 0))
                                            n_downrate = fmt_speed(n_data.get("downrate", 0))
                                            notes.append(f"حقيقة هامة: العميل استهلك كامل باقته. السرعة الحالية المخفضة هي {n_downrate} تحميل و {n_uprate} رفع. وهو بحاجة إلى شحن باقة إضافية لتعود سرعته الأصلية ({downrate} تحميل و {uprate} رفع).")
                                    else:
                                        notes.append(f"حقيقة هامة: العميل استهلك كامل باقته وسرعته مخفضة حالياً. سرعته الأصلية هي {downrate} تحميل و {uprate} رفع.")
                                else:
                                    notes.append(f"حقيقة: السرعة الحالية لباقة العميل هي {downrate} تحميل و {uprate} رفع بسعر {price} ل.س.")
                                    if next_prof_id:
                                        next_prof_res = self._crm_client.get_profile(next_prof_id)
                                        if next_prof_res.get("success") and "data" in next_prof_res:
                                            n_data = next_prof_res.get("data", {}).get("data", {})
                                            n_uprate = fmt_speed(n_data.get("uprate", 0))
                                            n_downrate = fmt_speed(n_data.get("downrate", 0))
                                            notes.append(f"حقيقة هامة: عند انتهاء باقة العميل الحالية (إذا استهلك كامل الحجم)، ستنخفض سرعته تلقائياً لتصبح {n_downrate} تحميل و {n_uprate} رفع.")
                                
                    if search_res and search_res.get("success") and "data" in search_res:
                            s_data = search_res.get("data", {})
                            if isinstance(s_data, dict) and s_data.get("data"):
                                s_data = s_data["data"]
                                
                            # Find exact user
                            target_user = None
                            if isinstance(s_data, list):
                                for u in s_data:
                                    if u.get("username") == username:
                                        target_user = u
                                        break
                                        
                            if target_user and "status" in target_user:
                                stat = target_user["status"]
                                is_traffic_ok = stat.get("traffic", True)
                                is_online = stat.get("online", False)
                                
                                if not is_traffic_ok:
                                    notes.append("حقيقة هامة: باقة العميل انتهت حالياً (استهلك كامل الحجم المخصص)، ولذلك سرعته مخفضة أو متوقفة.")
                                    if 'original_speed_note' in locals():
                                        notes.append(original_speed_note)
                                else:
                                    notes.append("حقيقة: باقة العميل لم تنتهِ وحجم الباقة لا يزال متاحاً للاستخدام.")
                                    
                                if is_online:
                                    notes.append("حقيقة: الراوتر الخاص بالعميل متصل بالإنترنت حالياً (Online).")
                                else:
                                    notes.append("حقيقة: الراوتر الخاص بالعميل غير متصل بالإنترنت حالياً (Offline).")
                                    
                    # Router Live Rate (From Parallel Fetch)
                    if rate_res and rate_res.get("success") and "data" in rate_res:
                        r_data = rate_res.get("data", {})
                        if isinstance(r_data, dict):
                            actual_rate_data = r_data.get("data", r_data)
                            if isinstance(actual_rate_data, dict) and "rate" in actual_rate_data:
                                rate = actual_rate_data["rate"]
                                notes.append(f"حقيقة هامة للتشخيص: السرعة الفعلية المسحوبة حالياً (اللحظية) من الراوتر هي: {rate}")
                            
                    # Freeze logic
                    if data.get("freezed") == 1:
                        notes.append("حقيقة هامة: حساب العميل مجمد حالياً (يحتاج للتواصل مع الدعم الفني لإعادة تفعيله).")
                        
                    # Account Status logic
                    acc_status = data.get("status")
                    if acc_status == 0:
                        notes.append("حقيقة هامة: حساب العميل معطل حالياً (Disabled)، ويجب عليه التواصل مع الدعم الفني لإعادة تفعيله.")

                    # Connection Type logic (user_type field)
                    user_type = data.get("user_type")
                    if user_type == 0:
                        notes.append("حقيقة: نوع اشتراك العميل هو شبكة أرضية (ADSL).")
                    elif user_type == 1:
                        notes.append("حقيقة: نوع اشتراك العميل هو لاسلكي (WIFI Outdoor).")
                        
                    # Discount logic
                    dt = data.get("discount_type")
                    da = data.get("discount_amount")
                    if dt and dt != "none":
                        if dt == "all":
                            notes.append("حقيقة: العميل لديه خصم كامل (مجاني) على فواتيره.")
                        elif dt == "part":
                            notes.append(f"حقيقة: العميل لديه خصم جزئي بقيمة {da} على فواتيره.")
                            
                    # MAC Binding logic
                    cpe_mac = data.get("cpe_mac")
                    if cpe_mac:
                        notes.append(f"حقيقة هامة للتشخيص: حساب العميل مربوط بـ MAC Address محدد وهو ({cpe_mac}). إذا ذكر العميل أنه قام بتغيير الراوتر الخاص به براوتر جديد وهو لا يعمل بينما القديم يعمل، فهذا يعني أن المشكلة هي 'حماية الماك' ويجب عليه التواصل مع الدعم الفني لإلغاء ربط الماك القديم.")
                            
                    # Pending profile change
                    hupc = data.get("has_unprocessed_profile_change")
                    if hupc is not None:
                        if hupc:
                            notes.append("حقيقة: يوجد طلب تغيير سرعة أو باقة للعميل وهو قيد المعالجة حالياً.")
                        else:
                            notes.append("حقيقة: لا يوجد أي طلب تغيير سرعة أو باقة قيد المعالجة للعميل حالياً.")

                    # IPTV Logic
                    iptv_type = data.get("iptv_type")
                    iptv_pkg = data.get("iptv_package")
                    if iptv_type == "none" or not iptv_type:
                        notes.append("حقيقة: العميل غير مشترك بخدمة التلفزيون (IPTV) حالياً.")
                    elif iptv_type == "pro":
                        notes.append(f"حقيقة: العميل مشترك بخدمة التلفزيون IPTV (نسخة Pro) وباقته هي ({iptv_pkg}). إذا استفسر عن الروابط، زوده برابط تطبيق Hyper IPTV Pro: https://proiptv.io/login/")
                    elif iptv_type == "like":
                        notes.append(f"حقيقة: العميل مشترك بخدمة التلفزيون IPTV (نسخة Like) وباقته هي ({iptv_pkg}). إذا استفسر عن الروابط، زوده برابط تطبيق Hyper IPTV Like: https://likesyria.sy/login")

                    # Try to fetch IPTV expiration if they are subscribed
                    if iptv_type and iptv_type != "none":
                        try:
                            if iptv_res.get("success") and "data" in iptv_res:
                                iptv_data = iptv_res["data"]
                                if isinstance(iptv_data, dict) and "data" in iptv_data:
                                    exp_date = iptv_data["data"].get("expiration_date")
                                    if exp_date:
                                        if exp_date == "غير مسجل":
                                            notes.append("حقيقة: حساب العميل غير مسجل بعد في نظام الـ IPTV (لا يوجد تاريخ انتهاء فعلي).")
                                        else:
                                            notes.append(f"حقيقة: تاريخ انتهاء اشتراك خدمة التلفزيون (IPTV) هو: {exp_date}")
                        except Exception as e:
                            logger.error(f"Failed to process IPTV expiration: {e}")

                    if notes:
                        data["ai_business_logic_notes"] = notes
                        
                    # Remove raw technical fields to avoid confusing the LLM
                    fields_to_remove = [
                        "status", "profile_id", "profile_type", 
                        "iptv_type", "user_type", 
                        "profile_details", "parent_id", "freezed"
                    ]
                    for f in fields_to_remove:
                        data.pop(f, None)
                        
                    # Only fetch and inject the packages if the requested tool is get_available_packages
                    if tool_name == "get_available_packages":
                        if 'user_profile_type' in locals() and user_profile_type == 4:
                            notes.append("تنبيه هام جداً: العميل يمتلك باقة غير محدودة (Unlimited)، لذلك يمنع منعاً باتاً تفعيل أي باقات إضافية له.")
                            data["ai_business_logic_notes"] = notes
                            data["available_topup_packages"] = []
                        else:
                            user_balance = 0.0
                            if "balance" in data:
                                try:
                                    user_balance = float(data["balance"])
                                except (ValueError, TypeError):
                                    pass

                            used_loan_amount = 0.0
                            logger.info(f"Fetched invoices for {customer_id}: {inv_res}")
                            if inv_res.get("success") and "data" in inv_res:
                                inv_data_payload = inv_res["data"]
                                inv_data = []
                                if isinstance(inv_data_payload, dict):
                                    inv_data = inv_data_payload.get("data", [])
                                elif isinstance(inv_data_payload, list):
                                    inv_data = inv_data_payload
                                for inv in inv_data:
                                    if isinstance(inv, dict):
                                        paid_val = inv.get("paid")
                                        is_unpaid = (paid_val == 0 or paid_val == "0" or paid_val is False)
                                        if inv.get("type") == "pkg_activation" and is_unpaid:
                                            amt = 0.0
                                            try:
                                                amt = float(inv.get("amount", inv.get("total", 0)))
                                            except:
                                                pass
                                            used_loan_amount += amt

                            if res_pkg and res_pkg.get("success") and "data" in res_pkg:
                                api_json = res_pkg["data"]
                                if isinstance(api_json, dict) and "data" in api_json:
                                    packages = api_json["data"]
                                    if isinstance(packages, list):
                                        filtered_packages = []
                                        for p in packages:
                                            if p.get("enabled"):
                                                quota_mb_str = p.get("quota_mb", "0")
                                                try:
                                                    quota_gb = float(quota_mb_str) / 1024
                                                except ValueError:
                                                    quota_gb = 0
                                                    
                                                pkg_price = 0.0
                                                try:
                                                    pkg_price = float(p.get("price", 0))
                                                except ValueError:
                                                    pass

                                                pkg_id = p.get("id")
                                                pkg_name = p.get("name", "")
                                                
                                                can_activate = False
                                                loan_note = ""
                                                if user_balance >= pkg_price:
                                                    can_activate = True
                                                else:
                                                    if (used_loan_amount + pkg_price) <= 50:
                                                        can_activate = True
                                                        loan_note = " (ستتم إضافة التكلفة كسلفة على الفاتورة القادمة)"
                                                
                                                if can_activate:
                                                    filtered_packages.append({
                                                        "name": pkg_name + loan_note,
                                                        "quota_gb": f"{quota_gb:g} GB",
                                                        "price": p.get("price")
                                                    })
                                                    notes.append(f'[ACTION_BUTTON: {{"text": "تفعيل {pkg_name}", "callback_data": "req_activate_pkg_{pkg_id}"}}]')
                                                else:
                                                    filtered_packages.append({
                                                        "name": pkg_name + " (الرصيد غير كافٍ)",
                                                        "quota_gb": f"{quota_gb:g} GB",
                                                        "price": p.get("price")
                                                    })
                                                    
                                        data["available_topup_packages"] = filtered_packages
                                        
                            if notes:
                                data["ai_business_logic_notes"] = notes
                        
                return response
                
            elif tool_name == "get_troubleshooting_data":
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                    
                # 1. Fetch overview
                overview = self._crm_client.get_user_overview(customer_id)
                data = overview.get("data", {}) if overview.get("success") else {}
                
                # 2. Fetch rate, sessions, profile in parallel
                profile_id = data.get("profile_id")
                
                import concurrent.futures
                
                def fetch_rate():
                    return self._crm_client.get_user_current_rate(customer_id)
                def fetch_sessions():
                    return self._crm_client.get_user_sessions(customer_id, limit=5)
                def fetch_profile():
                    return self._crm_client.get_profile(profile_id) if profile_id else {}
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    f_rate = executor.submit(fetch_rate)
                    f_sessions = executor.submit(fetch_sessions)
                    f_profile = executor.submit(fetch_profile)
                    
                    try:
                        rate = f_rate.result()
                        if rate.get("success"):
                            data["current_rate"] = rate.get("data")
                    except Exception as e:
                        logger.warning(f"Failed to fetch rate: {e}")
                        
                    try:
                        sessions = f_sessions.result()
                        if sessions.get("success"):
                            data["recent_sessions"] = sessions.get("data", {}).get("data", [])
                    except Exception as e:
                        logger.warning(f"Failed to fetch sessions: {e}")
                        
                    try:
                        prof_res = f_profile.result()
                        if prof_res.get("success") and "data" in prof_res:
                            prof_data = prof_res.get("data", {}).get("data", {})
                            data["profile_details"] = prof_data
                    except Exception as e:
                        logger.warning(f"Failed to fetch profile: {e}")

                # 5. Provide Action Button for Disconnect and Connection Type
                conn_type_note = "ADSL" if "ADSL" in str(data.get("profile_name", "")).upper() else "Wi-Fi/Microwave"
                data["ai_business_logic_notes"] = [
                    f"حقيقة هامة: نوع اشتراك هذا العميل هو ({conn_type_note}). استخدم هذه المعلومة لتحديد مسار التشخيص المناسب.",
                    "تعليمات لك: إذا قررت أنه يجب فصل الجلسة كجزء من عملية الإصلاح، أطلب من العميل الضغط على الزر أدناه.",
                    '[ACTION_BUTTON: {"text": "إعادة تهيئة الاتصال (فصل الجلسة)", "callback_data": "req_disconnect_session"}]'
                ]
                
                return {"success": True, "data": data}
                
            elif tool_name == "check_extend_status":
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                
                # Fetch username and expiration first
                overview = self._crm_client.get_user_overview(customer_id)
                username = None
                expiration = None
                if overview.get("success") and "data" in overview:
                    username = overview["data"].get("username")
                    expiration = overview["data"].get("expiration")
                    
                if not username:
                    return {"success": False, "error": "Could not determine username"}
                    
                # Prevent extension if expired > 3 days
                if expiration:
                    try:
                        from datetime import datetime
                        # e.g., '2024-05-10 12:00:00'
                        exp_date = datetime.strptime(str(expiration)[:19], "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        diff_days = (now - exp_date).days
                        if diff_days >= 3:
                            notes = [
                                f"حقيقة: حساب العميل منتهي الصلاحية منذ فترة طويلة (انتهى في {expiration}).",
                                "حقيقة: الحد الأقصى المسموح به للتمديد هو 3 أيام فقط كحد أقصى إجمالاً.",
                                "تعليمات لك: اعتذر من العميل وأخبره أنه لا يمكنه الاستفادة من خدمة التمديد لأن اشتراكه منتهي منذ أكثر من 3 أيام، وعملية التمديد لن تكون كافية لإعادة تفعيل الخدمة. اطلب منه تجديد اشتراكه (Top-up)."
                            ]
                            return {"success": True, "data": {"extend_bill_value": -2, "ai_business_logic_notes": notes}}
                    except Exception as e:
                        logger.warning(f"Failed to parse expiration date {expiration}: {e}")
                    
                # Fetch extend status
                ext_status = self._crm_client.get_extend_status(username)
                if ext_status.get("success") and "data" in ext_status:
                    val = ext_status["data"].get("extend_bill")
                    notes = []
                    if val == 0:
                        notes.append("حقيقة: يمكن للعميل تمديد صلاحية حسابه. كل ضغطة تمدد الحساب ليوم واحد مجاناً.")
                        notes.append("حقيقة هامة: الحد الأقصى المسموح به لعدد أيام التمديد هو 3 أيام فقط ولا يمكن تجاوزه.")
                        notes.append("تعليمات لك: أخبر العميل أنه يمكنه طلب تمديد الصلاحية، ووضّح له أنه إذا كان اشتراكه منتهياً منذ عدة أيام، سيحتاج لتكرار العملية لتغطية الأيام الفائتة (بحد أقصى 3 مرات).")
                        notes.append('[ACTION_BUTTON: {"text": "تأكيد التمديد (مجاني)", "callback_data": "req_extend_bill"}]')
                    elif val == 27:
                        notes.append("حقيقة: يمكن للعميل تمديد صلاحية حسابه بتكلفة 27 ل.س لكل يوم إضافي يتم تمديده.")
                        notes.append("حقيقة هامة: الحد الأقصى المسموح به لعدد أيام التمديد هو 3 أيام فقط ولا يمكن تجاوزه.")
                        notes.append("تعليمات لك: أخبر العميل أنه يمكنه التمديد بتكلفة 27 ليرة سورية، ووضّح أنه يحتاج تكرار العملية إذا كان متأخراً أكثر من يوم (بحد أقصى 3 مرات).")
                        notes.append('[ACTION_BUTTON: {"text": "تأكيد التمديد (27 ل.س)", "callback_data": "req_extend_bill"}]')
                    elif val == -1 or val == "-1":
                        notes.append("حقيقة: لقد استنفد العميل الحد الأقصى لأيام التمديد (3 أيام). لا يمكنه التمديد أكثر.")
                        notes.append("تعليمات لك: اعتذر من العميل وأخبره أنه استنفد الحد الأقصى المسموح به للتمديد (3 أيام) ولا يمكن تمديد الصلاحية أكثر.")
                    else:
                        notes.append(f"حقيقة: حالة التمديد غير معروفة ({val}). يرجى طلب التواصل مع الدعم الفني.")
                        
                    return {"success": True, "data": {"extend_bill_value": val, "ai_business_logic_notes": notes}}
                else:
                    return {"success": False, "error": "Failed to fetch extend status"}
                    
            elif tool_name == "disconnect_user":
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                return self._crm_client.disconnect_user(customer_id)
                
            elif tool_name == "get_user_sessions":
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                limit = parameters.get("limit", 30)
                return self._crm_client.get_user_sessions(customer_id, limit)
            elif tool_name == "get_invoice_amount":
                username = parameters.get("username")
                if not username:
                    return {"success": False, "error": "Username required for invoice amount"}
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                
                response = self._crm_client.get_invoice_amount(username)
                
                # Add AI business logic notes to help the LLM interpret the invoice
                if response.get("success") and "data" in response:
                    data = response["data"]
                    notes = []
                    notes.append("حقيقة: هذه تفاصيل فاتورة العميل بناءً على رصيده والخدمات المفعلة.")
                    
                    if data.get("is_overdue"):
                        notes.append("حقيقة هامة جداً: الفاتورة (مستحقة الدفع حالياً overdue). يجب على العميل دفعها لكي لا تنقطع الخدمة أو لكي يتم تفعيلها.")
                    else:
                        notes.append("حقيقة هامة جداً: الفاتورة (غير مستحقة حالياً incoming). هذا المبلغ هو ما سيدفعه العميل في الدورة القادمة أو عند التجديد القادم، وقد يتغير.")
                    
                    notes.append(f"إجمالي المبلغ قبل أي خصم (total_amount): {data.get('total_amount')} ل.س")
                    
                    if "discount_amount" in data and data.get("discount_amount") != 0:
                        dt = data.get('discount_type', 'none')
                        dt_arabic = "لا يوجد"
                        if dt == "all":
                            dt_arabic = "خصم كامل (مجاني)"
                        elif dt == "part":
                            dt_arabic = "خصم جزئي"
                            
                        notes.append(f"نوع الخصم: {dt_arabic}")
                        notes.append(f"قيمة الخصم: {abs(data.get('discount_amount', 0))} ل.س")
                        
                    notes.append(f"القيمة النهائية المطلوب دفعها (بعد الخصم) (final_amount): {data.get('final_amount')} ل.س")
                    
                    if data.get("adsl_service_amount", 0) > 0:
                        notes.append(f"ملاحظة: هذا يتضمن اشتراك الإنترنت (ADSL) بقيمة {data.get('adsl_service_amount')} ل.س لمدة {data.get('adsl_monthes')} شهر.")
                        
                    if data.get("iptv_service_amount", 0) > 0:
                        notes.append(f"ملاحظة: هذا يتضمن اشتراك التلفزيون (IPTV) بقيمة {data.get('iptv_service_amount')} ل.س.")
                    
                    if data.get("packages_amount", 0) > 0:
                        notes.append(f"ملاحظة: يوجد ديون باقات مفعلة لم يتم دفعها بقيمة {data.get('packages_amount')} ل.س.")
                    
                    if data.get("days_extends_amount", 0) > 0:
                        notes.append(f"ملاحظة: يوجد مبلغ {data.get('days_extends_amount')} ل.س تكلفة أيام التمديد (لـ {data.get('total_extends')} أيام).")
                        
                    data["ai_business_logic_notes"] = notes
                
                return response
                
            elif tool_name == "get_invoices":
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                return self._crm_client.get_user_invoices(customer_id)
                
            elif tool_name == "extend_bill":
                username = parameters.get("username")
                if not username:
                    return {"success": False, "error": "Username required"}
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                return self._crm_client.extend_user_bill(username)
                
            else:
                return {"success": False, "error": f"Tool {tool_name} is not implemented yet in ToolExecutor."}
                
        except (PermissionDeniedException, AgentEmergencyStopException):
            raise  # never swallow permission errors
        except requests.RequestException as e:
            logger.error(f"CRM API request failed: {e}")
            return {"success": False, "error": f"Failed to connect to CRM API: {e}"}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}
