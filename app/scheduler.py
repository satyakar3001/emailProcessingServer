import logging
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db, Email
from app.email_service import EmailService
from app.ml_classifier import EmailClassifier

logger = logging.getLogger(__name__)

class EmailScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.email_service = EmailService()
        self.classifier = EmailClassifier()
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            try:
                # Add the email processing job to run every 30 minutes
                self.scheduler.add_job(
                    func=self.process_emails_job,
                    trigger=IntervalTrigger(minutes=settings.SCHEDULER_INTERVAL_MINUTES),
                    id='email_processor',
                    name='Process emails every 30 minutes',
                    replace_existing=True
                )
                
                # Add a job to run immediately on startup
                self.scheduler.add_job(
                    func=self.process_emails_job,
                    trigger='date',
                    id='email_processor_startup',
                    name='Process emails on startup'
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info(f"Email scheduler started - running every {settings.SCHEDULER_INTERVAL_MINUTES} minutes")
                
            except Exception as e:
                logger.error(f"Error starting scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            try:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Email scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
    
    def process_emails_job(self):
        """Main job function that processes emails"""
        logger.info("Starting email processing job")
        start_time = time.time()
        
        try:
            # Get database session
            db = next(get_db())
            
            # Retrieve emails from different sources
            all_emails = []
            
            # Generate sample emails for testing (this will always work!)
            sample_emails = self.email_service.generate_sample_emails(count=settings.SAMPLE_EMAILS_COUNT)
            all_emails.extend(sample_emails)
            logger.info(f"Generated {len(sample_emails)} sample emails for testing")
            
            # If configured to use sample emails only, skip external email retrieval
            if settings.USE_SAMPLE_EMAILS_ONLY:
                logger.info("Using sample emails only - skipping external email retrieval")
            else:
                # Try to retrieve from Outlook (optional)
                if settings.OUTLOOK_EMAIL and settings.OUTLOOK_PASSWORD:
                    try:
                        outlook_emails = self.email_service.retrieve_outlook_emails(max_count=20)
                        all_emails.extend(outlook_emails)
                        logger.info(f"Retrieved {len(outlook_emails)} emails from Outlook")
                    except Exception as e:
                        logger.warning(f"Could not retrieve Outlook emails: {e}")
                else:
                    logger.info("Outlook not configured - skipping Outlook email retrieval")
                
                # Try to retrieve from Gmail (optional)
                if settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET:
                    try:
                        gmail_emails = self.email_service.retrieve_gmail_emails(max_count=20)
                        all_emails.extend(gmail_emails)
                        logger.info(f"Retrieved {len(gmail_emails)} emails from Gmail")
                    except Exception as e:
                        logger.warning(f"Could not retrieve Gmail emails: {e}")
                else:
                    logger.info("Gmail not configured - skipping Gmail email retrieval")
            
            if not all_emails:
                logger.warning("No emails retrieved from any source")
                return
            
            # Save emails to JSON for backup (path determined by service using BACKUP_DIR)
            json_filename = self.email_service.save_emails_to_json(all_emails)
            
            # Process each email
            processed_count = 0
            problem_count = 0
            
            for email_data in all_emails:
                try:
                    # Check if email already exists
                    existing_email = db.query(Email).filter(Email.email_id == email_data.email_id).first()
                    if existing_email:
                        logger.debug(f"Email {email_data.email_id} already exists, skipping")
                        continue
                    
                    # Classify the email
                    is_problem, category, confidence = self.classifier.classify_email(
                        email_data.subject, 
                        email_data.content
                    )
                    
                    # Create email record
                    db_email = Email(
                        email_id=email_data.email_id,
                        sender=email_data.sender,
                        recipient=email_data.recipient,
                        subject=email_data.subject,
                        content=email_data.content,
                        received_date=email_data.received_date,
                        is_problem=is_problem,
                        category=category if is_problem else None,
                        confidence_score=confidence
                    )
                    
                    # Add to database
                    db.add(db_email)
                    processed_count += 1
                    
                    if is_problem:
                        problem_count += 1
                        logger.info(f"Problem email detected: {email_data.subject} - Category: {category}")
                    else:
                        logger.debug(f"Information email: {email_data.subject}")
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_data.email_id}: {e}")
                    continue
            
            # Commit all changes
            db.commit()
            
            # Log summary
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(
                f"Email processing completed in {duration:.2f}s - "
                f"Processed: {processed_count}, Problems: {problem_count}, "
                f"Backup saved to: {json_filename}"
            )
            
        except Exception as e:
            logger.error(f"Error in email processing job: {e}")
        finally:
            try:
                db.close()
            except:
                pass
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "next_run": None if not self.is_running else str(self.scheduler.get_job('email_processor').next_run_time),
            "interval_minutes": settings.SCHEDULER_INTERVAL_MINUTES,
            "job_count": len(self.scheduler.get_jobs())
        }
    
    def trigger_manual_run(self):
        """Manually trigger email processing"""
        logger.info("Manual email processing triggered")
        self.process_emails_job()

# Global scheduler instance
email_scheduler = EmailScheduler()
