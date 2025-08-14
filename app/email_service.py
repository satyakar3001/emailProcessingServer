import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from exchangelib import Credentials, Account, DELEGATE, Configuration
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as GoogleCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.config import settings
from app.models import EmailCreate

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.outlook_account = None
        self.gmail_service = None
        self.setup_email_services()
    
    def setup_email_services(self):
        """Setup Outlook and Gmail connections"""
        try:
            # Setup Outlook
            if settings.OUTLOOK_EMAIL and settings.OUTLOOK_PASSWORD:
                credentials = Credentials(settings.OUTLOOK_EMAIL, settings.OUTLOOK_PASSWORD)
                config = Configuration(server=settings.OUTLOOK_SERVER, credentials=credentials)
                self.outlook_account = Account(
                    primary_smtp_address=settings.OUTLOOK_EMAIL,
                    config=config,
                    autodiscover=False,
                    access_type=DELEGATE
                )
                logger.info("Outlook connection established")
            
            # Setup Gmail
            if settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET:
                # Gmail setup would require OAuth2 flow
                # For now, we'll use the credentials if available
                logger.info("Gmail credentials configured")
                
        except Exception as e:
            logger.error(f"Error setting up email services: {e}")
    
    def generate_sample_emails(self, count: int = 10) -> List[EmailCreate]:
        """Generate sample emails for testing purposes"""
        sample_emails = []
        
        # Sample email templates
        email_templates = [
            {
                "sender": "support@company.com",
                "subject": "Your account has been suspended due to suspicious activity",
                "content": "We detected unusual login attempts from multiple locations. Your account has been temporarily suspended for security reasons. Please contact our support team immediately.",
                "is_problem": True,
                "category": "security_concern"
            },
            {
                "sender": "billing@company.com", 
                "subject": "Payment failed - Action required",
                "content": "Your recent payment of $99.99 has failed. Please update your payment method to avoid service interruption.",
                "is_problem": True,
                "category": "billing_problem"
            },
            {
                "sender": "tech@company.com",
                "subject": "System maintenance scheduled for tonight",
                "content": "We will be performing scheduled maintenance tonight from 2-4 AM EST. Some services may be temporarily unavailable.",
                "is_problem": False,
                "category": None
            },
            {
                "sender": "noreply@company.com",
                "subject": "Welcome to our platform!",
                "content": "Thank you for joining our platform. We're excited to have you on board!",
                "is_problem": False,
                "category": None
            },
            {
                "sender": "alerts@company.com",
                "subject": "Service outage detected in US East region",
                "content": "We're experiencing technical difficulties in our US East region. Our team is working to resolve this issue as quickly as possible.",
                "is_problem": True,
                "category": "service_outage"
            },
            {
                "sender": "dev@company.com",
                "subject": "Bug report: Login page not loading",
                "content": "Users are reporting that the login page is not loading properly. This appears to be affecting all browsers and devices.",
                "is_problem": True,
                "category": "technical_issue"
            },
            {
                "sender": "newsletter@company.com",
                "subject": "Monthly newsletter - March 2024",
                "content": "Check out our latest updates, new features, and upcoming events in this month's newsletter.",
                "is_problem": False,
                "category": None
            },
            {
                "sender": "admin@company.com",
                "subject": "Password reset request",
                "content": "You requested a password reset. Click the link below to set a new password. If you didn't request this, please ignore this email.",
                "is_problem": False,
                "category": None
            },
            {
                "sender": "monitoring@company.com",
                "subject": "High CPU usage detected on server-01",
                "content": "Server server-01 is experiencing unusually high CPU usage (95%). This may impact application performance.",
                "is_problem": True,
                "category": "performance_problem"
            },
            {
                "sender": "data@company.com",
                "subject": "Data backup completed successfully",
                "content": "Your data backup has been completed successfully. All files have been securely stored.",
                "is_problem": False,
                "category": None
            }
        ]
        
        # Generate emails with timestamps
        for i in range(min(count, len(email_templates))):
            template = email_templates[i]
            received_date = datetime.now() - timedelta(hours=i*2)  # Spread emails over time
            
            email = EmailCreate(
                email_id=f"sample_{uuid.uuid4().hex[:8]}",
                sender=template["sender"],
                recipient="user@company.com",
                subject=template["subject"],
                content=template["content"],
                received_date=received_date
            )
            sample_emails.append(email)
        
        return sample_emails
    
    def retrieve_outlook_emails(self, max_count: int = 50) -> List[EmailCreate]:
        """Retrieve emails from Outlook MS 365"""
        emails = []
        
        if not self.outlook_account:
            logger.warning("Outlook account not configured")
            return emails
        
        try:
            # Get emails from inbox
            inbox = self.outlook_account.inbox
            messages = inbox.all().order_by('-datetime_received')[:max_count]
            
            for message in messages:
                try:
                    email = EmailCreate(
                        email_id=message.message_id or str(uuid.uuid4()),
                        sender=message.sender.email_address,
                        recipient=message.to_recipients[0].email_address if message.to_recipients else "",
                        subject=message.subject or "",
                        content=message.body or "",
                        received_date=message.datetime_received
                    )
                    emails.append(email)
                except Exception as e:
                    logger.error(f"Error processing Outlook message: {e}")
                    continue
            
            logger.info(f"Retrieved {len(emails)} emails from Outlook")
            
        except Exception as e:
            logger.error(f"Error retrieving Outlook emails: {e}")
        
        return emails
    
    def retrieve_gmail_emails(self, max_count: int = 50) -> List[EmailCreate]:
        """Retrieve emails from Gmail"""
        emails = []
        
        if not (settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET):
            logger.warning("Gmail credentials not configured")
            return emails
        
        try:
            # Gmail API implementation would go here
            # For now, return empty list as it requires OAuth2 setup
            logger.info("Gmail retrieval not yet implemented - requires OAuth2 setup")
            
        except Exception as e:
            logger.error(f"Error retrieving Gmail emails: {e}")
        
        return emails
    
    def save_emails_to_json(self, emails: List[EmailCreate], filename: str = None) -> str:
        """Save emails to a JSON file in the configured backup directory"""
        import os
        # Ensure backup directory exists
        backup_dir = settings.BACKUP_DIR
        os.makedirs(backup_dir, exist_ok=True)

        # If no filename provided, create one inside backup dir
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(backup_dir, f"emails_backup_{timestamp}.json")
        else:
            # If a relative filename without directory is provided, place it under backup dir
            if not os.path.isabs(filename) and os.path.dirname(filename) in ("", "."):
                filename = os.path.join(backup_dir, filename)

        # Ensure target directory exists
        target_dir = os.path.dirname(filename) or "."
        os.makedirs(target_dir, exist_ok=True)
        
        # Convert to dict for JSON serialization
        email_dicts = []
        for email in emails:
            email_dict = {
                "email_id": email.email_id,
                "sender": email.sender,
                "recipient": email.recipient,
                "subject": email.subject,
                "content": email.content,
                "received_date": email.received_date.isoformat()
            }
            email_dicts.append(email_dict)
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(email_dicts, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(emails)} emails to {filename}")
        return filename
    
    def load_emails_from_json(self, filename: str) -> List[EmailCreate]:
        """Load emails from a JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                email_dicts = json.load(f)
            
            emails = []
            for email_dict in email_dicts:
                # Parse datetime string back to datetime object
                received_date = datetime.fromisoformat(email_dict["received_date"])
                
                email = EmailCreate(
                    email_id=email_dict["email_id"],
                    sender=email_dict["sender"],
                    recipient=email_dict["recipient"],
                    subject=email_dict["subject"],
                    content=email_dict["content"],
                    received_date=received_date
                )
                emails.append(email)
            
            logger.info(f"Loaded {len(emails)} emails from {filename}")
            return emails
            
        except Exception as e:
            logger.error(f"Error loading emails from JSON: {e}")
            return []
