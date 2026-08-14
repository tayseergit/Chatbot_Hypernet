"""
Tool Executor — connects CRM tools directly to the live HyperCRM API.

LAYER 3 ENFORCEMENT: Final hard guard before any HTTP call to CRM.
Even if Layer 2 (WorkflowCoordinator) is bypassed somehow, this layer
checks permissions again before sending any data to the CRM system.
"""
import os
from application.monitoring.logger import AppLogger
from application.shared.exceptions.permission_exceptions import (
    PermissionDeniedException,
    AgentEmergencyStopException,
)
from backend_service.crm.crm_client import CRMClient

logger = AppLogger.get_logger("tool_executor")


class ToolExecutor:
    """
    Executes live HyperCRM tools via CRMClient with token auth and Layer 3 permission guards.
    """

    def __init__(self, permission_service=None):
        self._permission_svc = permission_service
        self._crm_client = CRMClient()

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

        logger.info(f"Executing tool '{tool_name}' against real HyperCRM with params {parameters}")

        try:
            customer_id = parameters.get("crm_customer_id") or parameters.get("customer_id")

            if tool_name in ("get_balance", "get_current_package", "get_customer_info"):
                if not customer_id:
                    return {"success": False, "error": "Customer ID is required."}
                
                # Fetch user overview from real HyperCRM API
                overview_res = self._crm_client.get_user_overview(str(customer_id))
                if overview_res.get("success") and "data" in overview_res:
                    return {"success": True, "data": overview_res["data"]}
                return overview_res

            elif tool_name == "get_invoices":
                if not customer_id:
                    return {"success": False, "error": "Customer ID is required."}
                return self._crm_client.get_user_invoices(str(customer_id))

            elif tool_name == "extend_bill":
                username = parameters.get("username")
                if not username:
                    return {"success": False, "error": "Username is required."}
                return self._crm_client.extend_user_bill(username)

            elif tool_name == "check_phone_number":
                phone = parameters.get("phone", "")
                res = self._crm_client.search_user_by_phone(phone)
                return res

<<<<<<< HEAD
                    # Try to fetch IPTV expiration if they are subscribed
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
                                            amt = float(inv.get("amount", inv.get("total", 0)))
                                        except:
                                            pass
                                        used_loan_amount += amt

                        res_pkg = self._crm_client.get_available_packages(customer_id)
                        if res_pkg.get("success") and "data" in res_pkg:
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
                
                # 2. Fetch rate
                try:
                    rate = self._crm_client.get_user_current_rate(customer_id)
                    if rate.get("success"):
                        data["current_rate"] = rate.get("data")
                except Exception as e:
                    logger.warning(f"Failed to fetch rate: {e}")
                    
                # 3. Fetch sessions
                try:
                    sessions = self._crm_client.get_user_sessions(customer_id, limit=5)
                    if sessions.get("success"):
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
<<<<<<< HEAD
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
=======
                # Create ticket in real HyperCRM
                return self._crm_client.post(
                    f"{self._crm_client._auth_manager._base_url}/tickets",
                    parameters
                )
>>>>>>> 79b10e8 (feat: complete dashboard frontend with integrated action logs, enterprise copy, and pure MySQL setup)

            else:
                # Direct method dispatch if available on CRMClient
                if hasattr(self._crm_client, tool_name):
                    method = getattr(self._crm_client, tool_name)
                    return method(**parameters)
                return {"success": False, "error": f"Tool '{tool_name}' is not recognized."}

        except (PermissionDeniedException, AgentEmergencyStopException):
            raise
        except Exception as e:
            logger.error(f"Tool execution error against HyperCRM: {e}")
            return {"success": False, "error": f"فشل الاتصال بنظام CRM: {str(e)}"}
