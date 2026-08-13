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
        self._app.add_handler(
<<<<<<< HEAD
            MessageHandler((filters.TEXT | filters.CONTACT | filters.PHOTO) & ~filters.COMMAND, self._handle_message)
=======
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
>>>>>>> c78e952 (feat: add dashboard frontend, permissions system, action logs, and new database setup)
        )

        self._logger.info("Telegram bot started — polling for messages...")
        print("[BOT] Telegram bot is running! Send messages to your bot.")
        
        while True:
            try:
                self._app.run_polling(drop_pending_updates=True)
                break
            except Exception as e:
                self._logger.error(f"Network or connection error in Telegram bot: {e}")
                print(f"[BOT WARNING] Connection lost: {e}. Retrying in 5 seconds...")
                import time
                time.sleep(5)

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

<<<<<<< HEAD
    async def _handle_logout(self, update, context) -> None:
        """Handle /logout or /reset command."""
        user_id = str(update.effective_user.id)
        response_msg = await asyncio.to_thread(self._facade.logout_user, user_id)
        from telegram import ReplyKeyboardRemove
        await update.message.reply_text(response_msg, reply_markup=ReplyKeyboardRemove())

    async def _handle_callback_query(self, update, context) -> None:
        """Handle inline button clicks."""
        query = update.callback_query
        user_id = str(query.from_user.id)
        action_data = query.data
        
        if action_data == "ignore":
            await query.answer()
            return
            
        if action_data == "req_extend_bill":
            await query.answer()
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [
                [InlineKeyboardButton("نعم، تأكيد التمديد", callback_data="confirm_extend_bill"),
                 InlineKeyboardButton("لا، إلغاء", callback_data="cancel_extend_bill")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            return
            
        if action_data == "cancel_extend_bill":
            await query.answer("تم الإلغاء")
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [[InlineKeyboardButton("❌ تم الإلغاء", callback_data="ignore")]]
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if action_data == "confirm_extend_bill":
            await query.answer("جاري معالجة طلبك...")
            self._logger.info(f"User {user_id} triggered action: {action_data}")
            
            # Disable button visually
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [[InlineKeyboardButton("✅ تمت الموافقة", callback_data="ignore")]]
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                self._logger.warning(f"Could not edit message markup: {e}")
            
            # Execute action via facade
            result_msg = await asyncio.to_thread(self._facade.execute_action, user_id, action_data)
            
            # Send result as a new message so it's clear
            await context.bot.send_message(chat_id=query.message.chat_id, text=result_msg)
            return

        if action_data == "req_disconnect_session":
            await query.answer("جاري إرسال أمر الفصل...")
            self._logger.info(f"User {user_id} triggered action: {action_data}")
            
            # Disable button visually
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [[InlineKeyboardButton("⏳ جاري الفصل...", callback_data="ignore")]]
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception:
                pass
            
            # Execute action via facade
            result_msg = await asyncio.to_thread(self._facade.execute_action, user_id, action_data)
            
            # Send result as a new message
            await context.bot.send_message(chat_id=query.message.chat_id, text=result_msg)
            
            # Mark original as done
            keyboard_done = [[InlineKeyboardButton("✅ انتهت العملية", callback_data="ignore")]]
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard_done))
            except Exception:
                pass
            return

        if action_data.startswith("req_activate_pkg_"):
            pkg_id = action_data.replace("req_activate_pkg_", "")
            await query.answer()
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [
                [InlineKeyboardButton("نعم، تأكيد الشراء والتفعيل", callback_data=f"confirm_activate_pkg_{pkg_id}")],
                [InlineKeyboardButton("لا، إلغاء", callback_data="cancel_activate_pkg")]
            ]
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                self._logger.warning(f"Could not edit message markup: {e}")
            return
            
        if action_data == "cancel_activate_pkg":
            await query.answer("تم الإلغاء")
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [[InlineKeyboardButton("❌ تم الإلغاء", callback_data="ignore")]]
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception:
                pass
            return

        if action_data.startswith("confirm_activate_pkg_"):
            real_action_data = action_data.replace("confirm_", "") # becomes activate_pkg_{pkg_id}
            await query.answer("جاري معالجة طلبك...")
            self._logger.info(f"User {user_id} triggered action: {real_action_data}")
            
            # Disable button visually
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [[InlineKeyboardButton("⏳ جاري المعالجة...", callback_data="ignore")]]
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                self._logger.warning(f"Could not edit message markup: {e}")
            
            # Execute action via facade
            result_msg = await asyncio.to_thread(self._facade.execute_action, user_id, real_action_data)
            
            # Send result as a new message so it's clear
            await context.bot.send_message(chat_id=query.message.chat_id, text=result_msg)
            
            # Mark original as done
            keyboard_done = [[InlineKeyboardButton("✅ انتهت العملية", callback_data="ignore")]]
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard_done))
            except Exception:
                pass
            return

    async def _handle_message(self, update, context) -> None:
        """Handle incoming text, voice, and photo messages — main handler."""
        user_id = str(update.effective_user.id)
        u = update.effective_user
        user_name = f"{u.first_name or ''} {u.last_name or ''}".strip()
        if u.username:
            user_name += f" (@{u.username})"
        if not user_name:
            user_name = f"مشترك تلجرام ({user_id})"

        message = update.effective_message
        image_bytes = None
        image_path = None

        if message.contact:
            message_text = message.contact.phone_number
        elif message.voice:
            try:
                voice_file = await message.voice.get_file()
                voice_bytes = await voice_file.download_as_bytearray()
                message_text = await asyncio.to_thread(self._voice_service.transcribe, bytes(voice_bytes))
            except Exception as e:
                self._logger.error(f"Voice transcription failed: {e}")
                await message.reply_text("عذراً، تعذر الاستماع إلى الرسالة الصوتية. يرجى إرسالها نصياً.")
                return
        elif message.photo:
            message_text = message.caption or "صورة لقيم الراوتر"
            try:
                photo_file = await message.photo[-1].get_file()
                byte_array = await photo_file.download_as_bytearray()
                image_bytes = bytes(byte_array)

                # Save image to disk for logging
                import os, time
                media_dir = os.path.join(os.getcwd(), "media")
                os.makedirs(media_dir, exist_ok=True)
                file_path = os.path.join(media_dir, f"{user_id}_{int(time.time())}.jpg")
                with open(file_path, "wb") as f:
                    f.write(image_bytes)
                image_path = file_path
                self._logger.info(f"Saved image from {user_id} to {file_path}")
            except Exception as e:
                self._logger.error(f"Failed to download photo: {e}")
        else:
            message_text = message.text or ""

        if not message_text and not image_bytes:
            return

        self._logger.info(f"Telegram message from {user_name} ({user_id}): {message_text[:100]}")

        try:
            # Send typing indicator
            await update.effective_chat.send_action("typing")

            # Process through facade
            response = await asyncio.to_thread(
                self._facade.handle_message, user_id, message_text, user_name=user_name, image_bytes=image_bytes, image_path=image_path
            )

            # Check for inline action buttons in response
            keyboard = []
            clean_text = response.text
            import re, json
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton

            btn_pattern = r'\[ACTION_BUTTON:\s*(\{.*?\})\]'
            matches = re.findall(btn_pattern, clean_text)
            for m in matches:
                try:
                    btn_data = json.loads(m)
                    keyboard.append([InlineKeyboardButton(btn_data["text"], callback_data=btn_data["callback_data"])])
                except Exception as e:
                    self._logger.warning(f"Failed to parse ACTION_BUTTON: {e}")

            clean_text = re.sub(btn_pattern, '', clean_text).strip()
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

            await message.reply_text(
                clean_text,
                reply_markup=reply_markup
            )

            self._logger.info(
                f"Replied to {user_id} | intent={response.intent} "
                f"sources={response.sources_used}"
            )

        except Exception as e:
            self._logger.error(f"Error handling Telegram message: {e}")
            await message.reply_text(SUPPORT_FALLBACK_MESSAGE)
