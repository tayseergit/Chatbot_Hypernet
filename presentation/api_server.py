import os
import time
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

def create_app(facade) -> FastAPI:
    app = FastAPI(title="ISP Chatbot API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup_event():
        import threading
        token = facade._config.telegram.bot_token
        if token:
            from presentation.telegram_bot import TelegramBot
            bot = TelegramBot(token, facade)
            t = threading.Thread(target=bot.start, daemon=True)
            t.start()
            print("Telegram bot started in background thread.")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.post("/api/chat")
    async def chat_endpoint(
        user_id: str = Form(...),
        message: str = Form(""),
        image: Optional[UploadFile] = File(None)
    ):
        """
        API endpoint for chat messages, supporting text and optional image uploads.
        """
        image_bytes = None
        image_path = None
        
        if image and image.filename:
            image_bytes = await image.read()
            # Save image to media directory exactly like Telegram bot does
            media_dir = os.path.join(os.getcwd(), "media")
            os.makedirs(media_dir, exist_ok=True)
            file_path = os.path.join(media_dir, f"{user_id}_{int(time.time())}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            image_path = file_path

        import asyncio
        response = await asyncio.to_thread(
            facade.handle_message, user_id, message, image_bytes, image_path
        )

        return {
            "intent": response.intent,
            "text": response.text,
            "actions": response.actions
        }

    @app.get("/api/traces")
    def get_traces():
        """
        API endpoint to read the traces.log file for the dashboard.
        """
        log_file = os.path.join(os.getcwd(), "logs", "traces.log")
        if not os.path.exists(log_file):
            return {"traces": []}
            
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Parse blocks separated by double newline
        blocks = content.split("\n\n")
        parsed_traces = []
        for block in blocks:
            if not block.strip():
                continue
            lines = block.strip().split("\n")
            if not lines:
                continue
                
            header = lines[0]
            if "[TRACE ID:" not in header:
                continue
                
            steps = []
            total_time = ""
            for line in lines[1:]:
                if line.startswith("  "):
                    steps.append(line.strip())
                elif line.startswith("Total Time:"):
                    total_time = line.replace("Total Time:", "").strip()
                    
            parsed_traces.append({
                "header": header,
                "steps": steps,
                "total_time": total_time
            })
            
        # Return newest first
        return {"traces": parsed_traces[::-1]}

    return app
