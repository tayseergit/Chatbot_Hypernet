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
# Defaulting to isp_chatbot as per the main branch
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
    # Don't eagerly connect here because the DB might not exist yet!
except Exception as e:
    logger.error(f"Failed to create SQLAlchemy engine: {e}")
    raise e

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

def init_db(drop_all: bool = False):
    """Initialize MySQL database tables. Auto-creates DB if it doesn't exist."""
    import pymysql

    try:
        if drop_all:
            logger.warning(f"Dropping and recreating database '{DB_NAME}' from scratch...")
            conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=int(DB_PORT), autocommit=True)
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
            cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.close()

        logger.info("Initializing MySQL database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info(f"MySQL database '{DB_NAME}' initialized successfully.")
        
    except Exception as e:
        logger.error(f"Failed to initialize MySQL database: {e}")
        # If the database doesn't exist, create it automatically (Best of both worlds)
        if "Unknown database" in str(e) or "1049" in str(e):
            logger.warning(f"Database '{DB_NAME}' does not exist. Creating it automatically...")
            try:
                conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=int(DB_PORT))
                conn.cursor().execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn.close()
                Base.metadata.create_all(bind=engine)
                logger.info(f"Database '{DB_NAME}' created and initialized successfully.")
            except Exception as creation_error:
                logger.error(f"Failed to create database: {creation_error}")
                raise
        else:
            raise

def get_db():
    """Dependency to get a MySQL DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
