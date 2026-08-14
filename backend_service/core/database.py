import sys
import platform
if sys.platform == "win32":
    if not hasattr(platform, "_wmi_query_patched"):
        platform._wmi_query = lambda *args, **kwargs: ('10.0.19041', 1, 'Multiprocessor Free', 0, 0)
        platform._wmi_query_patched = True

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("database")

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "isp_chatbot")

# Pure MySQL Connection String with utf8mb4 encoding
MYSQL_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

try:
    engine = create_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        connect_args={"connect_timeout": 5}
    )
    with engine.connect() as conn:
        pass
    logger.info(f"Connected to MySQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to MySQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}: {e}")
    raise e

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

def init_db(drop_all: bool = False):
    """Initialize MySQL database tables."""
    try:
        logger.info("Initializing MySQL database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info(f"MySQL database '{DB_NAME}' initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize MySQL database: {e}")

def get_db():
    """Dependency to get a MySQL DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
