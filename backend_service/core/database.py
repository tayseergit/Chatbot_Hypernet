 

import os
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, declarative_base
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("database")

# Load configuration from environment or use default XAMPP credentials
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")

# Default PyMySQL connection string
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db(drop_all: bool = False):
    """Initialize database tables."""
    import pymysql
    
    try:
        if drop_all:
            logger.warning(f"Dropping and recreating database '{DB_NAME}' from scratch...")
            # Connect to MySQL server without specifying the DB
            conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=int(DB_PORT), autocommit=True)
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            conn.close()
            
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # In case the database itself doesn't exist, try to create it
        if "Unknown database" in str(e):
            logger.warning(f"Database '{DB_NAME}' does not exist. Creating it...")
            try:
                import pymysql
                conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=int(DB_PORT))
                conn.cursor().execute(f"CREATE DATABASE {DB_NAME}")
                conn.close()
                Base.metadata.create_all(bind=engine)
                logger.info(f"Database '{DB_NAME}' created and initialized successfully.")
            except Exception as creation_error:
                logger.error(f"Failed to create database: {creation_error}")
                raise
        else:
            raise

def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
