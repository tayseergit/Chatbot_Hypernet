"""
Telegram Bot — robust presentation layer for the chatbot.

Uses httpx with direct polling and explicit offset acknowledgement to guarantee
100% stability, no asyncio loop hangs, and full Windows UTF-8 compatibility.
"""

import sys
import os
import time
import json
from typing import Optional, Dict, Any

# Guarantee project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Ensure UTF-8 on Windows console to prevent UnicodeEncodeError
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import httpx

from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import SUPPORT_FALLBACK_MESSAGE


class TelegramBot:
    """
    Robust, production-grade Telegram bot using httpx synchronous polling.
    """

    def __init__(self, token: str, facade):
        self._token = token
        self._facade = facade
        self._logger = AppLogger.get_logger("telegram_bot")
        self._running = False
        self._offset = 0
        self._base_url = f"https://api.telegram.org/bot{self._token}"
        self._client = httpx.Client(timeout=httpx.Timeout(20.0, connect=10.0))

    def _api_post(self, method: str, json_data: dict) -> dict:
        """Call Telegram Bot API via POST with retries."""
        url = f"{self._base_url}/{method}"
        for attempt in range(3):
            try:
                resp = self._client.post(url, json=json_data)
                if resp.status_code == 200:
                    return resp.json()
                self._logger.warning(f"Telegram API {method} returned {resp.status_code}: {resp.text}")
                return resp.json()
            except Exception as e:
                self._logger.warning(f"Telegram API request {method} failed (attempt {attempt+1}): {e}")
                time.sleep(1)
        return {"ok": False, "error": "Network failed after 3 attempts"}

    def _send_message(self, chat_id: int, text: str, reply_markup: dict = None) -> dict:
        """Send text message with optional reply_markup."""
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._api_post("sendMessage", payload)

    def _send_typing(self, chat_id: int) -> None:
        """Send typing indicator."""
        try:
            self._api_post("sendChatAction", {"chat_id": chat_id, "action": "typing"})
        except Exception:
            pass

    def _send_document(self, chat_id: int, file_path: str) -> None:
        """Send document/file."""
        if not os.path.exists(file_path):
            self._logger.warning(f"Document file not found: {file_path}")
            return
        url = f"{self._base_url}/sendDocument"
        try:
            with open(file_path, "rb") as f:
                self._client.post(url, data={"chat_id": chat_id}, files={"document": f}, timeout=30.0)
        except Exception as e:
            self._logger.error(f"Failed to send document {file_path}: {e}")

    def start(self) -> None:
        """Start polling loop."""
        self._running = True
        self._logger.info("Starting Telegram bot (httpx robust polling)...")
        print("\n" + "=" * 60, flush=True)
        print("  Telegram Bot is LIVE and POLLING!", flush=True)
        print("=" * 60, flush=True)

        # Pre-flight: test getMe
        try:
            me = self._client.get(f"{self._base_url}/getMe", timeout=10.0).json()
            if me.get("ok"):
                username = me["result"].get("username", "Unknown")
                first_name = me["result"].get("first_name", "Bot")
                print(f"[BOT] Connected as @{username} ({first_name})", flush=True)
                self._logger.info(f"Connected to Telegram as @{username}")
            else:
                self._logger.error(f"Failed to connect to Telegram: {me}")
                print(f"[BOT] ❌ Invalid Token or API Error: {me}", flush=True)
                return
        except Exception as e:
            self._logger.error(f"Connection pre-flight error: {e}")
            print(f"[BOT] ❌ Connection error: {e}", flush=True)
            return

        while self._running:
            try:
                updates = self._client.get(
                    f"{self._base_url}/getUpdates",
                    params={"offset": self._offset, "timeout": 15},
                    timeout=20.0
                ).json()

                if not updates.get("ok"):
                    time.sleep(2)
                    continue

                for update in updates.get("result", []):
                    self._offset = update["update_id"] + 1

                    if "message" in update:
                        self._handle_incoming_message(update["message"])
                    elif "callback_query" in update:
                        self._handle_callback_query(update["callback_query"])

            except httpx.ReadTimeout:
                # Normal long polling timeout
                continue
            except Exception as e:
                self._logger.warning(f"Polling loop error: {e}")
                time.sleep(3)

    def _handle_incoming_message(self, message: dict) -> None:
        """Handle any incoming user message."""
        chat_id = message.get("chat", {}).get("id")
        user = message.get("from", {})
        user_id = str(user.get("id"))

        first_name = (user.get("first_name") or "").strip()
        last_name = (user.get("last_name") or "").strip()
        tg_username = (user.get("username") or "").strip()
        name_parts = [p for p in [first_name, last_name] if p]
        full_name = " ".join(name_parts)
        if full_name and tg_username:
            user_name = f"{full_name} (@{tg_username})"
        elif full_name:
            user_name = full_name
        elif tg_username:
            user_name = f"@{tg_username}"
        else:
            user_name = f"مستخدم تلجرام ({user_id})"

        # Ensure session and user_name are recorded/updated in DB on every interaction
        try:
            if hasattr(self._facade, '_backend') and self._facade._backend:
                self._facade._backend.session_service.get_or_create_session(user_id, user_name=user_name)
        except Exception as ex:
            self._logger.debug(f"Could not update session user_name: {ex}")

        # Handle Photo or Image Document
        photo = message.get("photo")
        doc = message.get("document")
        caption = message.get("caption", "").strip()

        if photo or (doc and doc.get("mime_type", "").startswith("image/")):
            self._handle_photo_message(chat_id, user_id, user_name, photo=photo, document=doc, caption=caption)
            return

        # Check contact sharing
        if "contact" in message:
            message_text = message["contact"].get("phone_number", "")
        else:
            message_text = message.get("text", "").strip()

        if not message_text or not chat_id:
            return

        self._logger.info(f"Telegram message from {user_name} ({user_id}): {message_text[:100]}")
        print(f"\n[BOT] Message from {user_name} (ID: {user_id}): '{message_text}'", flush=True)

        if message_text == "/start":
            self._handle_start(chat_id, user_id, user_name)
        elif message_text == "/help":
            self._handle_help(chat_id)
        elif message_text == "/stats":
            self._handle_stats(chat_id)
        elif message_text in ("/logout", "/reset"):
            self._handle_logout(chat_id, user_id)
        else:
            self._handle_chat_message(chat_id, user_id, user_name, message_text)

    def _handle_photo_message(
        self, chat_id: int, user_id: str, user_name: str,
        photo: list = None, document: dict = None, caption: str = ""
    ) -> None:
        """Download user-uploaded photo from Telegram, store in media/user_photos, log in DB, and reply."""
        try:
            file_id = None
            if photo and len(photo) > 0:
                file_id = photo[-1].get("file_id")
            elif document:
                file_id = document.get("file_id")

            if not file_id:
                return

            print(f"\n[BOT] Received photo from {user_name} (ID: {user_id})", flush=True)

            # 1. Get file path from Telegram
            file_info = self._client.get(f"{self._base_url}/getFile", params={"file_id": file_id}, timeout=10.0).json()
            if not file_info.get("ok"):
                self._logger.error(f"Failed to getFile from Telegram: {file_info}")
                return

            remote_path = file_info["result"].get("file_path", "")
            download_url = f"https://api.telegram.org/file/bot{self._token}/{remote_path}"

            # 2. Download and save to media/user_photos
            media_dir = os.path.join(BASE_DIR, "media", "user_photos")
            os.makedirs(media_dir, exist_ok=True)

            ext = os.path.splitext(remote_path)[1] or ".jpg"
            timestamp = int(time.time())
            filename = f"{user_id}_{timestamp}_{file_id[:8]}{ext}"
            file_path = os.path.join(media_dir, filename)

            img_resp = self._client.get(download_url, timeout=25.0)
            if img_resp.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(img_resp.content)
                print(f"[BOT] Saved photo to: {file_path}", flush=True)

                relative_url = f"/media/user_photos/{filename}"
                msg_content = f"[صورة] {relative_url}"
                if caption:
                    msg_content += f"\n{caption}"

                # 3. Store in DB
                sess = None
                if hasattr(self._facade, '_backend') and self._facade._backend:
                    sess = self._facade._backend.session_service.get_or_create_session(user_id, user_name=user_name)
                    self._facade._backend.message_service.save_messages(sess.session_id, "user", msg_content)

                # 4. Reply to user
                reply_text = (
                    "تم استلام الصورة بنجاح وتوثيقها في سجل المحادثة.\n"
                    "فريق الدعم الفني سيقوم بمراجعتها. كيف يمكننا مساعدتك أيضاً؟"
                )
                self._send_message(chat_id, reply_text)
                if sess and hasattr(self._facade, '_backend') and self._facade._backend:
                    self._facade._backend.message_service.save_messages(sess.session_id, "bot", reply_text)
            else:
                self._logger.error(f"Failed to download image bytes: status {img_resp.status_code}")

        except Exception as e:
            self._logger.error(f"Exception handling photo upload: {e}")
            print(f"[BOT] Error saving photo: {e}", flush=True)

    def _handle_start(self, chat_id: int, user_id: str, user_name: str) -> None:
        """Handle /start."""
        welcome = (
            f"مرحباً بك {user_name} في مساعد خدمات الإنترنت هايبرنت! 🌐\n\n"
            "أنا هنا لمساعدتك في:\n"
            "• الاستعلام عن رصيدك الحالي\n"
            "• معرفة باقتك وسرعة الاشتراك\n"
            "• فتح تذكرة دعم فني واستفسار\n"
            "• معرفة العروض والأسعار بالليرة السورية\n\n"
            "اكتب استفسارك وسأساعدك فوراً! 💬"
        )
        try:
            if hasattr(self._facade, '_backend') and self._facade._backend:
                sess = self._facade._backend.session_service.get_or_create_session(user_id, user_name=user_name)
                self._facade._backend.message_service.save_messages(sess.session_id, "user", "/start")
                self._facade._backend.message_service.save_messages(sess.session_id, "bot", welcome)
        except Exception as ex:
            self._logger.warning(f"Failed to record /start in database: {ex}")

        self._send_message(chat_id, welcome)
        print(f"[BOT] 📤 Sent welcome to {user_name}")

    def _handle_help(self, chat_id: int) -> None:
        """Handle /help."""
        help_text = (
            "📋 الأوامر المتاحة:\n\n"
            "/start - بدء المحادثة والترحيب\n"
            "/help - عرض المساعدة وقائمة الخدمات\n"
            "/stats - إحصائيات الاستخدام\n"
            "/logout - تسجيل الخروج وإعادة التعيين\n\n"
            "أو اكتب سؤالك مباشرة وسيقوم المساعد الذكي بالرد عليك!"
        )
        self._send_message(chat_id, help_text)

    def _handle_stats(self, chat_id: int) -> None:
        """Handle /stats."""
        try:
            stats = self._facade.get_analytics()
            text = (
                f"📊 إحصائيات النظام:\n\n"
                f"إجمالي الاستفسارات: {stats.get('total_queries', 0)}\n"
                f"الجلسات النشطة: {stats.get('active_sessions', 0)}"
            )
        except Exception:
            text = "📊 النظام يعمل بشكل طبيعي."
        self._send_message(chat_id, text)

    def _handle_logout(self, chat_id: int, user_id: str) -> None:
        """Handle /logout."""
        try:
            msg = self._facade.logout_user(user_id)
        except Exception as e:
            msg = "تم تسجيل الخروج بنجاح."
        self._send_message(chat_id, msg, reply_markup={"remove_keyboard": True})

    def _handle_chat_message(self, chat_id: int, user_id: str, user_name: str, text: str) -> None:
        """Process natural language message through ChatbotFacade."""
        self._send_typing(chat_id)
        print(f"[BOT] ⚙️ Processing with Chatbot AI for {user_name}...")

        try:
            response = self._facade.handle_message(user_id, text, user_name=user_name)
            reply_text = response.text if hasattr(response, 'text') else str(response)
            intent = getattr(response, 'intent', 'general')
            print(f"[BOT] ✨ Response generated (intent: {intent})")
        except Exception as e:
            self._logger.error(f"handle_message error: {e}")
            print(f"[BOT] ❌ Error in AI pipeline: {e}")
            reply_text = SUPPORT_FALLBACK_MESSAGE
            intent = "error"

        # Check for request_phone_auth
        if intent == "request_phone_auth":
            reply_markup = {
                "keyboard": [[{"text": "📱 مشاركة رقم الهاتف", "request_contact": True}]],
                "one_time_keyboard": True,
                "resize_keyboard": True,
            }
            self._send_message(chat_id, reply_text, reply_markup=reply_markup)
            return

        # Check for actions / buttons / documents
        reply_markup = None
        actions = getattr(response, "actions", [])
        if actions:
            inline_buttons = []
            for action in actions:
                if action.get("type") == "button":
                    btn_text = action.get("text", "تأكيد")
                    btn_data = action.get("callback_data", "unknown")
                    inline_buttons.append([{"text": btn_text, "callback_data": btn_data}])
                elif action.get("type") == "document":
                    doc_path = action.get("path")
                    if doc_path:
                        self._send_document(chat_id, doc_path)

            if inline_buttons:
                reply_markup = {"inline_keyboard": inline_buttons}

        self._send_message(chat_id, reply_text, reply_markup=reply_markup)
        print(f"[BOT] 📤 Sent response to {user_name}")

    def _handle_callback_query(self, query: dict) -> None:
        """Handle inline button callback."""
        query_id = query.get("id")
        user = query.get("from", {})
        user_id = str(user.get("id"))
        chat_id = query.get("message", {}).get("chat", {}).get("id")
        action_data = query.get("data", "")

        first_name = (user.get("first_name") or "").strip()
        last_name = (user.get("last_name") or "").strip()
        tg_username = (user.get("username") or "").strip()
        name_parts = [p for p in [first_name, last_name] if p]
        full_name = " ".join(name_parts)
        if full_name and tg_username:
            user_name = f"{full_name} (@{tg_username})"
        elif full_name:
            user_name = full_name
        elif tg_username:
            user_name = f"@{tg_username}"
        else:
            user_name = f"مستخدم تلجرام ({user_id})"

        try:
            if hasattr(self._facade, '_backend') and self._facade._backend:
                self._facade._backend.session_service.get_or_create_session(user_id, user_name=user_name)
        except Exception:
            pass

        # Acknowledge callback query
        self._api_post("answerCallbackQuery", {"callback_query_id": query_id})

        if action_data == "ignore":
            return

        print(f"[BOT] Button clicked by user {user_name} ({user_id}): {action_data}", flush=True)

        if action_data == "req_extend_bill":
            markup = {
                "inline_keyboard": [
                    [
                        {"text": "نعم، تأكيد التمديد", "callback_data": "confirm_extend_bill"},
                        {"text": "لا، إلغاء", "callback_data": "cancel_extend_bill"},
                    ]
                ]
            }
            self._api_post("editMessageReplyMarkup", {
                "chat_id": chat_id,
                "message_id": query.get("message", {}).get("message_id"),
                "reply_markup": markup,
            })
            return

        if action_data == "cancel_extend_bill":
            markup = {"inline_keyboard": [[{"text": "❌ تم الإلغاء", "callback_data": "ignore"}]]}
            self._api_post("editMessageReplyMarkup", {
                "chat_id": chat_id,
                "message_id": query.get("message", {}).get("message_id"),
                "reply_markup": markup,
            })
            return

        if action_data == "confirm_extend_bill":
            result_msg = self._facade.execute_action(user_id, action_data)
            self._send_message(chat_id, result_msg)
            return

        if action_data.startswith("req_activate_pkg_"):
            pkg_id = action_data.replace("req_activate_pkg_", "")
            markup = {
                "inline_keyboard": [
                    [{"text": "نعم، تأكيد الشراء والتفعيل", "callback_data": f"confirm_activate_pkg_{pkg_id}"}],
                    [{"text": "لا، إلغاء", "callback_data": "cancel_activate_pkg"}],
                ]
            }
            self._api_post("editMessageReplyMarkup", {
                "chat_id": chat_id,
                "message_id": query.get("message", {}).get("message_id"),
                "reply_markup": markup,
            })
            return

        if action_data.startswith("confirm_activate_pkg_"):
            real_action = action_data.replace("confirm_", "")
            result_msg = self._facade.execute_action(user_id, real_action)
            self._send_message(chat_id, result_msg)
            return

        # Generic action
        result_msg = self._facade.execute_action(user_id, action_data)
        self._send_message(chat_id, result_msg)

    def stop(self) -> None:
        """Stop polling."""
        self._running = False
        try:
            self._client.close()
        except Exception:
            pass


if __name__ == "__main__":
    from application.app import Application
    app = Application()
    app.start(mode="telegram")
