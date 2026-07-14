"""Formatter — formats responses for Telegram output."""


from application.shared.configuration.app_config import SUPPORT_FALLBACK_MESSAGE


class ResponseFormatter:
    """Formats responses for Telegram, handling Arabic RTL and markdown."""

    def format_for_telegram(self, text: str) -> str:
        """Format text for Telegram delivery."""
        if not text:
            return SUPPORT_FALLBACK_MESSAGE

        # Clean up
        formatted = text.strip()

        # Ensure reasonable length for Telegram (4096 char limit)
        if len(formatted) > 4000:
            formatted = formatted[:3997] + "..."

        return formatted

    def format_error(self, error_msg: str) -> str:
        """Format an error message for the user."""
        return SUPPORT_FALLBACK_MESSAGE

    def format_greeting(self) -> str:
        """Default greeting when LLM is unavailable."""
        return "مرحباً بك! 👋\nأنا مساعدك الذكي لخدمات الإنترنت.\nكيف يمكنني مساعدتك اليوم؟"

    def format_goodbye(self) -> str:
        """Default goodbye message."""
        return "شكراً لتواصلك معنا! 🙏\nنتمنى لك يوماً سعيداً."
