"""
Tool Executor — connects CRM tools directly to the live HyperCRM API with Layer 3 Permission Guards.

LAYER 3 ENFORCEMENT: Final hard guard before any HTTP call to CRM.
Even if Layer 2 (WorkflowCoordinator) is bypassed somehow, this layer
checks permissions again before sending any data to the CRM system.
"""
import os
import requests
import time
from application.monitoring.logger import AppLogger
from application.shared.exceptions.permission_exceptions import (
    PermissionDeniedException,
    AgentEmergencyStopException,
)
from backend_service.crm.crm_client import CRMClient

logger = AppLogger.get_logger("tool_executor")
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "http://localhost:8090/api/crm")


class ToolExecutor:
    def __init__(self, permission_service=None, crm_client=None):
        self._permission_svc = permission_service
        self._crm_client = crm_client or CRMClient()

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
                response = self._crm_client.get_user_overview(str(customer_id))
                
                # 2. Apply business logic transformations to aid the LLM
                if response.get("success") and "data" in response:
                    data = response["data"]
                    notes = []
                    
                    user_profile_type = int(data.get("profile_type", 0))
                    
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
                    
                    if profile_id:
                        prof_res = self._crm_client.get_profile(profile_id)
                        if prof_res.get("success") and "data" in prof_res:
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
                                
                    if username:
                        search_res = self._crm_client.search_users(username)
                        if search_res.get("success") and "data" in search_res:
                            s_data = search_res.get("data", {})
                            if isinstance(s_data, dict) and s_data.get("data"):
                                user_item = s_data["data"][0] if isinstance(s_data["data"], list) else s_data["data"]
                                if isinstance(user_item, dict):
                                    data["user_type"] = user_item.get("user_type")
                                    data["profile_id"] = user_item.get("profile_id")
                                    data["status"] = user_item.get("status")
                                    data["freezed"] = user_item.get("freezed")
                                    data["parent_id"] = user_item.get("parent_id")
                                    data["iptv_type"] = user_item.get("iptv_type")
                                    
                    # Try to fetch IPTV expiration if they are subscribed
                    iptv_type = data.get("iptv_type")
                    if iptv_type and iptv_type != "none":
                        try:
                            iptv_res = self._crm_client.get_iptv_expiration(customer_id)
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
                            logger.error(f"Failed to fetch IPTV expiration: {e}")

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
                        user_balance = 0.0
                        if "balance" in data:
                            try:
                                user_balance = float(data["balance"])
                            except (ValueError, TypeError):
                                pass

                        used_loan_amount = 0.0
                        inv_res = self._crm_client.get_user_invoices(customer_id)
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
                                            amt = float(inv.get("amount", 0))
                                        except (ValueError, TypeError):
                                            amt = 0.0
                                        used_loan_amount += amt
                                        logger.info(f"Found unpaid loan invoice: {inv.get('id')} with amount {amt}")

                        # 3. Fetch available packages from CRM with eligibility filtering
                        packages_response = self._crm_client.get_available_packages(customer_id)
                        if packages_response.get("success") and "data" in packages_response:
                            all_pkgs = packages_response["data"].get("data", [])
                            
                            # Filter packages and build interactive buttons
                            eligible_pkgs = []
                            for pkg in all_pkgs:
                                try:
                                    price = float(pkg.get("price", 0))
                                except (ValueError, TypeError):
                                    price = 0.0
                                    
                                pkg_id = pkg.get("id")
                                
                                # Business Rule: Balance must cover Package Price + Unpaid Loans
                                if user_balance >= (price + used_loan_amount):
                                    pkg["can_buy"] = True
                                    pkg["action_button"] = f'[ACTION_BUTTON: {{"text": "تفعيل باقة {pkg.get("name")}", "callback_data": "req_activate_pkg_{pkg_id}"}}]'
                                else:
                                    pkg["can_buy"] = False
                                    pkg["action_button"] = None
                                    
                                eligible_pkgs.append(pkg)
                                
                            data["available_packages"] = eligible_pkgs
                            if "ai_business_logic_notes" not in data:
                                data["ai_business_logic_notes"] = []
                            data["ai_business_logic_notes"].append(
                                "حقيقة هامة: في حال رغبة العميل بتفعيل باقة وهو يمتلك رصيداً كافياً، يجب عليك استخدام صيغة الزر المرفق (ACTION_BUTTON) أسفل رسالتك لتمكينه من التفعيل بنقرة واحدة."
                            )

                    return {"success": True, "data": data}
                    
                return response
                
            elif tool_name == "troubleshoot_slow_internet" or tool_name == "dsl_line_values":
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                    
                # 1. Fetch user overview for profile and status
                overview = self._crm_client.get_user_overview(customer_id)
                data = {}
                if overview.get("success") and "data" in overview:
                    data = overview["data"]
                    
                # 2. Fetch live online/offline status
                status_res = self._crm_client.get_user_status(customer_id)
                if status_res.get("success") and "data" in status_res:
                    data["online_status"] = status_res["data"]
                    
                # 3. Fetch recent session logs
                try:
                    sessions = self._crm_client.get_user_sessions(customer_id, limit=5)
                    if sessions.get("success") and "data" in sessions:
                        data["recent_sessions"] = sessions.get("data", {}).get("data", [])
                except Exception as e:
                    logger.warning(f"Failed to fetch sessions: {e}")
                    
                # 4. Include profile details for speed comparison
                profile_id = data.get("profile_id")
                if profile_id:
                    prof_res = self._crm_client.get_profile(profile_id)
                    if prof_res.get("success") and "data" in prof_res:
                        prof_data = prof_res.get("data", {}).get("data", {})
                        data["profile_details"] = prof_data

                # 5. Provide Action Button for Disconnect and Connection Type
                conn_type_note = "ADSL" if "ADSL" in str(data.get("profile_name", "")).upper() else "Wi-Fi/Microwave"
                data["ai_business_logic_notes"] = [
                    f"حقيقة هامة: نوع اشتراك هذا العميل هو ({conn_type_note}). استخدم هذه المعلومة لتحديد مسار التشخيص المناسب.",
                    "تعليمات لك: إذا قررت أنه يجب فصل الجلسة كجزء من عملية الإصلاح، أطلب من العميل الضغط على الزر أدناه.",
                    '[ACTION_BUTTON: {"text": "إعادة تهيئة الاتصال (فصل الجلسة)", "callback_data": "req_disconnect_session"}]'
                ]
                
                return {"success": True, "data": data}
                
            elif tool_name == "open_ticket":
                if not self._crm_client:
                    return {"success": False, "error": "CRMClient not configured"}
                url = f"{self._crm_client._auth_manager._base_url}/tickets"
                return self._crm_client.post(url, parameters)
                
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
                return {"success": False, "error": f"Tool '{tool_name}' is not implemented in ToolExecutor."}

        except (PermissionDeniedException, AgentEmergencyStopException):
            raise  # never swallow permission errors
        except requests.RequestException as e:
            logger.error(f"CRM API request failed: {e}")
            return {"success": False, "error": f"Failed to connect to CRM API: {e}"}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}
