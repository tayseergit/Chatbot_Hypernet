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

MYSQL_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLITE_URL = "sqlite:///./chatbot_db.sqlite"

# Try MySQL first; fallback to SQLite if MySQL service is offline
try:
    # Force SQLite to bypass MySQL freeze on the system
    raise Exception("Bypass MySQL")
    # engine = create_engine(MYSQL_URL, pool_pre_ping=True, connect_args={"connect_timeout": 2})
    # with engine.connect() as conn:
    #     pass
    # logger.info(f"Connected to MySQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}")
except Exception as e:
    logger.warning(f"MySQL connection unavailable ({e}). Falling back to local SQLite database.")
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db(drop_all: bool = False):
    """Initialize database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
