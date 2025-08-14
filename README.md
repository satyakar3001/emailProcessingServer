# Email Processor FastAPI Server

A FastAPI-based email processing server that automatically retrieves emails from Outlook MS 365 and Gmail, classifies them using ML models, and stores categorized data in PostgreSQL.

## Features

- **Automated Email Processing**: Scheduler runs every 30 minutes to retrieve and process emails
- **ML-Powered Classification**: Uses Hugging Face models to categorize emails as problems or information
- **Multi-Platform Support**: Retrieves emails from Outlook MS 365 and Gmail
- **Smart Categorization**: Problem emails are further categorized into specific types (technical issues, billing problems, etc.)
- **PostgreSQL Storage**: Stores processed emails with classification results
- **RESTful API**: Comprehensive API endpoints for email management and monitoring
- **Sample Data Generation**: Built-in sample email generation for testing

## Architecture

```
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration and environment variables
│   ├── database.py          # Database models and connection
│   ├── models.py            # Pydantic schemas
│   ├── ml_classifier.py     # ML classification logic
│   ├── email_service.py     # Email retrieval services
│   ├── scheduler.py         # Background job scheduler
│   └── api.py              # FastAPI application and endpoints
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
└── README.md               # This file
```

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Outlook MS 365 account (optional)
- Gmail account with API credentials (optional)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd email_processor_fast-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Setup PostgreSQL database**
   ```sql
   CREATE DATABASE email_processor_db;
   ```

6. **Configure environment variables**
   Edit `.env` file with your settings:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/email_processor_db
   OUTLOOK_EMAIL=your_email@outlook.com
   OUTLOOK_PASSWORD=your_password
   GMAIL_CLIENT_ID=your_gmail_client_id
   GMAIL_CLIENT_SECRET=your_gmail_client_secret
   ```

## Usage

### Starting the Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### API Endpoints

#### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /scheduler/status` - Scheduler status

#### Email Management
- `GET /emails` - List emails with pagination and filters
- `GET /emails/{email_id}` - Get specific email
- `GET /emails/stats/summary` - Email statistics
- `POST /emails/process/manual` - Manually trigger email processing
- `POST /emails/generate-sample` - Generate sample emails for testing

#### Scheduler Control
- `POST /scheduler/start` - Start the scheduler
- `POST /scheduler/stop` - Stop the scheduler

#### ML Classification
- `POST /emails/classify` - Classify email text without storing

### Example API Usage

#### Generate Sample Emails
```bash
curl -X POST "http://localhost:8000/emails/generate-sample?count=5"
```

#### Get Email Statistics
```bash
curl "http://localhost:8000/emails/stats/summary"
```

#### Classify Email Text
```bash
curl -X POST "http://localhost:8000/emails/classify" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "subject=System Error&content=The application is not responding"
```

#### Get Emails with Filters
```bash
curl "http://localhost:8000/emails?is_problem=true&category=technical_issue&limit=10"
```

## Email Classification

The system uses ML models to classify emails into two main categories:

### 1. Problem vs Information
- **Problem**: Emails indicating issues, errors, or problems
- **Information**: General notifications, newsletters, confirmations

### 2. Problem Categories
When an email is classified as a problem, it's further categorized into:
- `technical_issue` - Bugs, errors, technical problems
- `billing_problem` - Payment issues, invoice problems
- `service_outage` - Service unavailability, downtime
- `account_access` - Login issues, password problems
- `data_issue` - Data corruption, loss, or access issues
- `performance_problem` - Slow performance, timeouts
- `security_concern` - Security breaches, unauthorized access
- `other` - General problems not fitting other categories

## Scheduler

The email scheduler runs automatically every 30 minutes (configurable) and:

1. Retrieves emails from configured sources (Outlook, Gmail)
2. Generates sample emails for testing
3. Classifies each email using ML models
4. Stores results in PostgreSQL database
5. Saves email backups to JSON files

## Configuration

Key configuration options in `.env`:

- `SCHEDULER_INTERVAL_MINUTES`: How often to process emails (default: 30)
- `HUGGINGFACE_MODEL_NAME`: ML model to use for classification
- `MODEL_PATH`: Local path for storing ML models
- `DATABASE_URL`: PostgreSQL connection string
- Email service credentials for Outlook and Gmail

## Development

### Project Structure
- **Models**: SQLAlchemy database models and Pydantic schemas
- **Services**: Business logic for email processing and ML classification
- **API**: FastAPI endpoints and request/response handling
- **Scheduler**: Background job management using APScheduler

### Adding New Email Sources
To add support for new email providers:

1. Extend `EmailService` class in `app/email_service.py`
2. Add configuration variables in `app/config.py`
3. Update the scheduler to use the new service

### Customizing ML Classification
To modify the classification logic:

1. Update `EmailClassifier` class in `app/ml_classifier.py`
2. Modify problem categories and their descriptions
3. Adjust confidence thresholds and fallback logic

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check `DATABASE_URL` in `.env`
   - Ensure database exists

2. **ML Model Loading Issues**
   - Check internet connection for model downloads
   - Verify `MODEL_PATH` directory exists
   - Check available disk space

3. **Email Service Errors**
   - Verify email credentials in `.env`
   - Check network connectivity
   - Ensure proper permissions for email access

### Logs
The application logs important events and errors. Check the console output or configure logging in `.env`:

```env
LOG_LEVEL=DEBUG
LOG_FILE=./logs/app.log
```


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please create an issue in the repository or contact the development team.
