"""
Application entry point — bootstraps and runs the AI ISP Chatbot.

Supports two modes:
1. Console mode: Interactive terminal for testing
2. Telegram mode: Connects to Telegram Bot API
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application.shared.configuration.app_config import AppConfig
from application.facade.chatbot_facade import ChatbotFacade
from application.monitoring.logger import AppLogger


class Application:
    """Main application class — bootstraps and manages the chatbot lifecycle."""

    def __init__(self, config: AppConfig = None):
        self._config = config or AppConfig.from_env()
        self._logger = AppLogger.get_logger(
            "app", level=self._config.monitoring.log_level, use_json=False,
        )
        self._facade: ChatbotFacade = None

    def start(self, knowledge_file: str = None, mode: str = "console") -> None:
        """
        Start the application.

        Args:
            knowledge_file: Path to XLS knowledge base file.
            mode: 'console' for interactive testing, 'telegram' for bot.
        """
        self._logger.info("Starting AI ISP Chatbot Platform...")

        # Initialize facade
        self._facade = ChatbotFacade(self._config)
        self._facade.initialize(knowledge_file)

        if mode == "telegram":
            self._run_telegram()
        else:
            self._run_console()

    def _run_console(self) -> None:
        """Run in interactive console mode for testing."""
        print("\n" + "=" * 60)
        print("  AI ISP Chatbot — Console Mode")
        print("  Type your message. Type 'quit' or 'exit' to stop.")
        print("  Type 'stats' to see analytics.")
        print("=" * 60 + "\n")

        user_id = "console_user_001"

        while True:
            try:
                message = input("\n🧑 You: ").strip()

                if not message:
                    continue
                if message.lower() in ("quit", "exit", "q"):
                    print("\nGoodbye! 👋")
                    break
                if message.lower() == "stats":
                    import json
                    stats = self._facade.get_analytics()
                    print("\n📊 Analytics:")
                    print(json.dumps(stats, indent=2, ensure_ascii=False))
                    continue

                # Process message through the full pipeline
                response = self._facade.handle_message(user_id, message)
                print(f"\n🤖 Bot: {response.text}")
                print(f"   [intent: {response.intent} | sources: {response.sources_used}]")

            except (KeyboardInterrupt, EOFError):
                print("\n\nShutting down...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

        self.shutdown()

    def _run_telegram(self) -> None:
        """Run in Telegram bot mode."""
        token = self._config.telegram.bot_token
        if not token:
            self._logger.error(
                "TELEGRAM_BOT_TOKEN not set. Set it via environment variable."
            )
            print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable.")
            return

        from application.presentation.telegram_bot import TelegramBot
        bot = TelegramBot(token, self._facade)
        bot.start()

    def shutdown(self) -> None:
        """Graceful shutdown."""
        if self._facade:
            self._facade.shutdown()
        self._logger.info("Application shutdown complete")


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="AI ISP Chatbot Platform")
    parser.add_argument("--mode", choices=["console", "telegram"],
                        default="console", help="Run mode")
    parser.add_argument("--knowledge", type=str, default=None,
                        help="Path to XLS knowledge base file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    config = AppConfig.from_env()
    if args.debug:
        config.debug = True
        config.monitoring.log_level = "DEBUG"

    app = Application(config)
    app.start(knowledge_file=args.knowledge, mode=args.mode)


if __name__ == "__main__":
    main()
