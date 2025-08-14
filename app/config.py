import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/email_processor_db")
    
    # Email Configuration
    OUTLOOK_EMAIL: Optional[str] = os.getenv("OUTLOOK_EMAIL")
    OUTLOOK_PASSWORD: Optional[str] = os.getenv("OUTLOOK_PASSWORD")
    OUTLOOK_SERVER: str = os.getenv("OUTLOOK_SERVER", "outlook.office365.com")
    
    GMAIL_CLIENT_ID: Optional[str] = os.getenv("GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET: Optional[str] = os.getenv("GMAIL_CLIENT_SECRET")
    GMAIL_REFRESH_TOKEN: Optional[str] = os.getenv("GMAIL_REFRESH_TOKEN")
    
    # Scheduler
    SCHEDULER_INTERVAL_MINUTES: int = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "30"))
    SAMPLE_EMAILS_COUNT: int = int(os.getenv("SAMPLE_EMAILS_COUNT", "10"))
    USE_SAMPLE_EMAILS_ONLY: bool = os.getenv("USE_SAMPLE_EMAILS_ONLY", "True").lower() == "true"
    
    # ML Model
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models")
    HUGGINGFACE_MODEL_NAME: str = os.getenv("HUGGINGFACE_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/app.log")

    # Backups
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", "./emails_backup")

    # Jira Integration
    JIRA_BASE_URL: Optional[str] = os.getenv("JIRA_BASE_URL")
    JIRA_EMAIL: Optional[str] = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN")
    JIRA_PROJECT_KEY: Optional[str] = os.getenv("JIRA_PROJECT_KEY")
    JIRA_ISSUE_TYPE: str = os.getenv("JIRA_ISSUE_TYPE", "Task")

settings = Settings()
