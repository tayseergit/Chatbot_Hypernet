"""Allowed intents for the AI ISP Chatbot."""

from typing import Dict, List

# Fallback keywords for graceful degradation
INTENT_KEYWORDS: Dict[str, List[str]] = {
    "billing": ["رصيد", "رصيدي", "كم رصيدي", "حسابي", "فاتورة", "فواتير", "دفع", "sداد"],
    "extend_bill": ["تمديد", "دين", "أيام إضافية", "يومين", "سلفة", "استلاف"],
    "wireless_packages": ["باقة", "باقتي", "package", "اشتراك", "باقات", "العروض", "وايرلس"],
    "contacts": ["تذكرة", "بلاغ", "شكوى", "مشكلة", "ticket", "عطل", "دعم فني"],
    "troubleshoot_slow_internet": ["بطيء", "ضعيف", "slow", "ضعف"],
    "dsl_troubleshooting": ["انقطاع", "واي فاي", "wifi", "راوتر", "كيف", "شلون"],
}

INTENT_SERVICE_MAP: Dict[str, List[str]] = {
    "billing": ["CRM"],
    "extend_bill": ["CRM"],
    "wireless_packages": ["CRM", "RAG"],
    "contacts": ["CRM"],
    "troubleshoot_slow_internet": ["CRM"],
    "dsl_troubleshooting": ["RAG", "CRM"],
}

ALLOWED_INTENTS = [
    "services",
    "dsl_troubleshooting",
    "troubleshoot_slow_internet",
    "dsl_line_values",
    "dsl_router",
    "dsl_sessions",
    "dsl_speed_change",
    "wireless_packages",
    "wireless_topup",
    "wireless_support",
    "wireless_signal",
    "iptv_service",
    "iptv_support",
    "iptv_packages",
    "iptv_fees",
    "static_ip",
    "extend_bill",
    "billing",
    "subscription",
    "sales_routing",
    "contacts",
    "adsl_packages",
    "package_price_adsl",
    "service_fees",
    "bot_channel",
    "bot_language",
    "bot_auth",
    "bot_account_info",
    # "bot_speed_change",
    "bot_package_charging",
    "bot_knowledge",
    "bot_escalation",
    "bot_availability",
]
