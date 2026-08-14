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
                MessageHandler, CallbackQueryHandler, filters,
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
        self._app.add_handler(CallbackQueryHandler(self._handle_callback_query))
        self._app.add_handler(
            MessageHandler((filters.TEXT | filters.CONTACT | filters.PHOTO | filters.VOICE | filters.AUDIO) & ~filters.COMMAND, self._handle_message)
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
        """Handle incoming text messages — main handler."""
        if update.edited_message:
            return  # Ignore edited messages
            
        message = update.message
        if not message:
            return
            
        user_id = str(update.effective_user.id)
        
        image_bytes = None
        image_path = None
        if message.contact:
            message_text = message.contact.phone_number
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
        elif message.voice or message.audio:
            media = message.voice or message.audio
            
            # File size limit check (5 MB)
            if media.file_size > 5 * 1024 * 1024:
                await message.reply_text("❌ عذراً، حجم المقطع الصوتي كبير جداً (يجب أن لا يتجاوز 5 ميغابايت).")
                return

            await message.chat.send_action("record_voice")
            message_text = None
            try:
                media_file = await media.get_file()
                byte_array = await media_file.download_as_bytearray()
                
                import os, time
                media_dir = os.path.join(os.getcwd(), "media")
                os.makedirs(media_dir, exist_ok=True)
                
                ext = ".ogg" if message.voice else ".mp3"
                file_path = os.path.join(media_dir, f"voice_{user_id}_{int(time.time())}{ext}")
                with open(file_path, "wb") as f:
                    f.write(byte_array)
                
                self._logger.info(f"Saved voice message to {file_path}. Transcribing...")
                
                from application.shared.utils.transcriber import AudioTranscriber
                transcriber = AudioTranscriber()
                message_text = await asyncio.to_thread(transcriber.transcribe, file_path)
                image_path = file_path  # Set this so it gets stored in DB
                
                self._logger.info(f"Transcription result: {message_text}")
                
                if not message_text:
                    await message.reply_text("❌ عذراً، لم أتمكن من فهم المقطع الصوتي.")
                    return
                    
            except Exception as e:
                self._logger.error(f"Failed to process voice message: {e}")
                await message.reply_text("❌ حدث خطأ أثناء معالجة المقطع الصوتي.")
                return
        else:
            message_text = message.text

        if not message_text and not image_bytes:
            return

        self._logger.info(f"Telegram message from {user_id}: {message_text[:100]}")

        try:
            # Send typing indicator
            await message.chat.send_action("typing")

            # Process through facade
            response = await asyncio.to_thread(
                self._facade.handle_message, user_id, message_text, image_bytes, image_path
            )

            # Check if we need to request phone number
            if response.intent == "request_phone_auth":
                from telegram import ReplyKeyboardMarkup, KeyboardButton
                contact_btn = KeyboardButton("📱 مشاركة رقم الهاتف", request_contact=True)
                reply_markup = ReplyKeyboardMarkup([[contact_btn]], one_time_keyboard=True, resize_keyboard=True)
                await message.reply_text(response.text, reply_markup=reply_markup)
            else:
                from telegram import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
                
                # Check for actions/buttons
                reply_markup = None
                if getattr(response, "actions", []):
                    keyboard = []
                    for action in response.actions:
                        if action.get("type") == "button":
                            btn_text = action.get("text", "تأكيد")
                            btn_data = action.get("callback_data", "unknown")
                            keyboard.append([InlineKeyboardButton(btn_text, callback_data=btn_data)])
                        elif action.get("type") == "document":
                            doc_path = action.get("path")
                            import os
                            if os.path.exists(doc_path):
                                try:
                                    with open(doc_path, 'rb') as f:
                                        await message.reply_document(document=f)
                                except Exception as e:
                                    self._logger.error(f"Failed to send document {doc_path}: {e}")
                            else:
                                self._logger.warning(f"Document not found at {doc_path}")

                    if keyboard:
                        reply_markup = InlineKeyboardMarkup(keyboard)
                
                if reply_markup is None:
                    reply_markup = ReplyKeyboardRemove()
                    
                await message.reply_text(response.text, reply_markup=reply_markup)

            self._logger.info(
                f"Replied to {user_id} | intent={response.intent} "
                f"sources={response.sources_used}"
            )

        except Exception as e:
            self._logger.error(f"Error handling Telegram message: {e}")
            await message.reply_text(SUPPORT_FALLBACK_MESSAGE)
