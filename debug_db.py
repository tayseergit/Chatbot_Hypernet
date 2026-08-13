import sys
import os
print("1")
from sqlalchemy import create_engine, text
print("2")
from sqlalchemy.orm import sessionmaker, declarative_base
print("3")
from application.monitoring.logger import AppLogger
print("4")
logger = AppLogger.get_logger("database")
print("5")
SQLITE_URL = "sqlite:///./chatbot_db.sqlite"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
print("6")
logger.warning("MySQL connection unavailable. Falling back to local SQLite database.")
print("7")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
print("8")
