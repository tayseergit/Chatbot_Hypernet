"""Formatter — formats responses for Telegram output."""


class ResponseFormatter:
    """Formats responses for Telegram, handling Arabic RTL and markdown."""

    def format_for_telegram(self, text: str) -> str:
        """Format text for Telegram delivery."""
        if not text:
            return "عذراً، حدث خطأ في معالجة طلبك."

        # Clean up
        formatted = text.strip()

        # Ensure reasonable length for Telegram (4096 char limit)
        if len(formatted) > 4000:
            formatted = formatted[:3997] + "..."

        return formatted

    def format_error(self, error_msg: str) -> str:
        """Format an error message for the user."""
        return f"⚠️ عذراً، {error_msg}\nيرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني."

    def format_greeting(self) -> str:
        """Default greeting when LLM is unavailable."""
        return "مرحباً بك! 👋\nأنا مساعدك الذكي لخدمات الإنترنت.\nكيف يمكنني مساعدتك اليوم؟"

    def format_goodbye(self) -> str:
        """Default goodbye message."""
        return "شكراً لتواصلك معنا! 🙏\nنتمنى لك يوماً سعيداً."
