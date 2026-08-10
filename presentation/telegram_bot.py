"""
Minimal Telegram Bot — presentation layer for the chatbot.

Uses python-telegram-bot library for Telegram Bot API integration.
Routes all messages through ChatbotFacade.
"""

import logging
import asyncio
from typing import Optional

from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import SUPPORT_FALLBACK_MESSAGE


class TelegramBot:
    """
    Minimal Telegram bot that routes messages to ChatbotFacade.

    Requires python-telegram-bot >= 20.0 installed.
    """

    def __init__(self, token: str, facade):
        self._token = token
        self._facade = facade
        self._logger = AppLogger.get_logger("telegram_bot")
        self._app = None

    def start(self) -> None:
        """Start the Telegram bot with polling."""
        try:
            from telegram import Update
            from telegram.ext import (
                ApplicationBuilder, CommandHandler,
                MessageHandler, filters,
            )
        except ImportError:
            self._logger.error(
                "python-telegram-bot not installed. "
                "Run: pip install python-telegram-bot"
            )
            print("ERROR: pip install python-telegram-bot")
            return

        self._logger.info("Starting Telegram bot...")

        self._app = ApplicationBuilder().token(self._token).build()

        # Register handlers
        self._app.add_handler(CommandHandler("start", self._handle_start))
        self._app.add_handler(CommandHandler("help", self._handle_help))
        self._app.add_handler(CommandHandler("stats", self._handle_stats))
        self._app.add_handler(CommandHandler("logout", self._handle_logout))
        self._app.add_handler(CommandHandler("reset", self._handle_logout))
        self._app.add_handler(
            MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, self._handle_message)
        )

        self._logger.info("Telegram bot started — polling for messages...")
        print("🤖 Telegram bot is running! Send messages to your bot.")
        self._app.run_polling()

    async def _handle_start(self, update, context) -> None:
        """Handle /start command."""
        user_id = str(update.effective_user.id)
        welcome = (
            "مرحباً بك في مساعد خدمات الإنترنت! 🌐\n\n"
            "أنا هنا لمساعدتك في:\n"
            "• الاستعلام عن رصيدك\n"
            "• معرفة باقتك الحالية\n"
            "• فتح تذكرة دعم فني\n"
            "• الإجابة على أسئلتك\n\n"
            "اكتب سؤالك وسأساعدك! 💬"
        )
        await update.message.reply_text(welcome)

    async def _handle_help(self, update, context) -> None:
        """Handle /help command."""
        help_text = (
            "📋 الأوامر المتاحة:\n\n"
            "/start - بدء المحادثة\n"
            "/help - عرض المساعدة\n"
            "/stats - إحصائيات الاستخدام\n\n"
            "أو اكتب سؤالك مباشرة!"
        )
        await update.message.reply_text(help_text)

    async def _handle_stats(self, update, context) -> None:
        """Handle /stats command."""
        import json
        stats = await asyncio.to_thread(self._facade.get_analytics)
        text = f"📊 إحصائيات النظام:\n\n"
        text += f"إجمالي الاستفسارات: {stats.get('total_queries', 0)}\n"
        text += f"الجلسات النشطة: {stats.get('active_sessions', 0)}\n"
        await update.message.reply_text(text)

    async def _handle_logout(self, update, context) -> None:
        """Handle /logout or /reset command."""
        user_id = str(update.effective_user.id)
        response_msg = await asyncio.to_thread(self._facade.logout_user, user_id)
        from telegram import ReplyKeyboardRemove
        await update.message.reply_text(response_msg, reply_markup=ReplyKeyboardRemove())

    async def _handle_message(self, update, context) -> None:
        """Handle incoming text messages — main handler."""
        user_id = str(update.effective_user.id)
        
        if update.message.contact:
            message_text = update.message.contact.phone_number
        else:
            message_text = update.message.text

        self._logger.info(f"Telegram message from {user_id}: {message_text[:100]}")

        try:
            # Send typing indicator
            await update.message.chat.send_action("typing")

            # Process through facade
            response = await asyncio.to_thread(
                self._facade.handle_message, user_id, message_text
            )

            # Check if we need to request phone number
            if response.intent == "request_phone_auth":
                from telegram import ReplyKeyboardMarkup, KeyboardButton
                contact_btn = KeyboardButton("📱 مشاركة رقم الهاتف", request_contact=True)
                reply_markup = ReplyKeyboardMarkup([[contact_btn]], one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text(response.text, reply_markup=reply_markup)
            else:
                from telegram import ReplyKeyboardRemove
                # Ensure keyboard is removed if previously sent
                await update.message.reply_text(response.text, reply_markup=ReplyKeyboardRemove())

            self._logger.info(
                f"Replied to {user_id} | intent={response.intent} "
                f"sources={response.sources_used}"
            )

        except Exception as e:
            self._logger.error(f"Error handling Telegram message: {e}")
            await update.message.reply_text(SUPPORT_FALLBACK_MESSAGE)
