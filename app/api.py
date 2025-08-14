from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.config import settings
from app.database import get_db, Email, JiraIssue, create_tables
from app.models import EmailResponse, EmailListResponse, HealthCheck
from app.scheduler import email_scheduler
from app.email_service import EmailService
from app.ml_classifier import EmailClassifier
from app.jira_service import JiraService

# Create FastAPI app
app = FastAPI(
    title="Email Processor API",
    description="FastAPI server for processing and classifying emails using ML",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
email_service = EmailService()
classifier = EmailClassifier()
jira_service = JiraService()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Create database tables
        create_tables()
        
        # Start the email scheduler
        email_scheduler.start()
        
        print("Application started successfully")
        print(f"Email scheduler running every {settings.SCHEDULER_INTERVAL_MINUTES} minutes")
        print(f"ML models loaded from {settings.HUGGINGFACE_MODEL_NAME}")
        
    except Exception as e:
        print(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        email_scheduler.stop()
        print("Application shutdown complete")
    except Exception as e:
        print(f"Error during shutdown: {e}")

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Email Processor API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db = next(get_db())
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check scheduler status
    scheduler_status = "healthy" if email_scheduler.is_running else "unhealthy"
    
    return HealthCheck(
        status="healthy" if db_status == "healthy" and scheduler_status == "healthy" else "unhealthy",
        timestamp=datetime.utcnow(),
        database=db_status,
        scheduler=scheduler_status
    )

@app.get("/emails", response_model=EmailListResponse)
async def get_emails(
    skip: int = Query(0, ge=0, description="Number of emails to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of emails to return"),
    is_problem: Optional[bool] = Query(None, description="Filter by problem status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get paginated list of emails with optional filters"""
    query = db.query(Email)
    
    # Apply filters
    if is_problem is not None:
        query = query.filter(Email.is_problem == is_problem)
    
    if category:
        query = query.filter(Email.category == category)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    emails = query.order_by(Email.received_date.desc()).offset(skip).limit(limit).all()
    
    return EmailListResponse(
        emails=[EmailResponse.from_orm(email) for email in emails],
        total=total
    )

@app.get("/emails/{email_id}", response_model=EmailResponse)
async def get_email(email_id: str, db: Session = Depends(get_db)):
    """Get a specific email by ID"""
    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return EmailResponse.from_orm(email)

@app.get("/emails/stats/summary")
async def get_email_stats(db: Session = Depends(get_db)):
    """Get email statistics summary"""
    try:
        total_emails = db.query(Email).count()
        problem_emails = db.query(Email).filter(Email.is_problem == True).count()
        info_emails = db.query(Email).filter(Email.is_problem == False).count()
        
        # Get category breakdown for problem emails
        category_stats = db.query(Email.category, db.func.count(Email.id)).filter(
            Email.is_problem == True,
            Email.category.isnot(None)
        ).group_by(Email.category).all()
        
        return {
            "total_emails": total_emails,
            "problem_emails": problem_emails,
            "information_emails": info_emails,
            "problem_categories": dict(category_stats),
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@app.post("/emails/process/manual")
async def process_emails_manual():
    """Manually trigger email processing"""
    try:
        email_scheduler.trigger_manual_run()
        return {"message": "Email processing triggered manually", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering email processing: {str(e)}")

@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and information"""
    return email_scheduler.get_status()

@app.post("/scheduler/start")
async def start_scheduler():
    """Start the email scheduler"""
    try:
        email_scheduler.start()
        return {"message": "Scheduler started successfully", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")

@app.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the email scheduler"""
    try:
        email_scheduler.stop()
        return {"message": "Scheduler stopped successfully", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")

@app.post("/integrations/jira/send-problems")
async def send_problem_emails_to_jira(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    """Create Jira issues for problem emails that don't yet have a Jira key."""
    if not jira_service.is_configured():
        raise HTTPException(status_code=400, detail="Jira is not configured")

    # Fetch problem emails that do not yet have a Jira issue linked
    subq = db.query(JiraIssue.email_id).subquery()
    emails = db.query(Email).filter(
        Email.is_problem == True,
        ~Email.id.in_(subq)
    ).order_by(Email.received_date.desc()).limit(limit).all()
    if not emails:
        return {"message": "No problem emails pending for Jira", "created": 0}

    created = 0
    failures = []
    for e in emails:
        summary = f"{e.subject} + {e.sender}"
        description = e.content or "(no content)"
        ok, key, err = await jira_service.create_issue(summary=summary[:255], description=description)
        if ok and key:
            db_issue = JiraIssue(email_id=e.id, issue_key=key)
            db.add(db_issue)
            created += 1
        else:
            failures.append({"email_id": e.email_id, "error": err})

    db.commit()
    return {"message": "Jira issue creation completed", "created": created, "failed": failures}

@app.post("/emails/generate-sample")
async def generate_sample_emails(count: int = Query(10, ge=1, le=50, description="Number of sample emails to generate")):
    """Generate sample emails for testing"""
    try:
        sample_emails = email_service.generate_sample_emails(count=count)
        
        # Save to JSON
        filename = email_service.save_emails_to_json(sample_emails)
        
        return {
            "message": f"Generated {len(sample_emails)} sample emails",
            "filename": filename,
            "count": len(sample_emails),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sample emails: {str(e)}")

@app.post("/emails/classify")
async def classify_email_text(subject: str, content: str):
    """Classify email text without storing in database"""
    try:
        is_problem, category, confidence = classifier.classify_email(subject, content)
        
        return {
            "is_problem": is_problem,
            "category": category,
            "confidence_score": confidence,
            "classification_timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error classifying email: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
