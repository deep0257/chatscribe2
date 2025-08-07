# ChatScribe - AI-Powered Document Assistant

A secure, modular web application built with FastAPI that allows authenticated users to upload documents (PDF, DOCX, TXT) and interact with an AI chatbot for document Q&A, summarization, and conversational analysis.

## Features

- **User Authentication**: Secure signup/login with JWT tokens and cookie-based session management
- **Document Upload**: Support for PDF, DOCX, and TXT files with text extraction
- **AI Chat Interface**: Intelligent Q&A and conversation about uploaded documents
- **Document Summarization**: AI-powered document summaries
- **Chat History**: Persistent chat sessions with user-specific storage
- **Responsive Web UI**: Clean, modern interface using Bootstrap and Jinja2 templates
- **RESTful API**: Complete API endpoints for programmatic access

## Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: OpenAI GPT, LangChain for document processing
- **Frontend**: HTML5, Bootstrap 5, Jinja2 templates
- **Authentication**: JWT tokens with secure cookie management
- **File Processing**: PyPDF2, python-docx for document parsing

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd chatscribe2
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/chatscribe
   SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

5. **Set up PostgreSQL**:
   - Install PostgreSQL
   - Create database: `CREATE DATABASE chatscribe;`
   - Update DATABASE_URL in `.env`

6. **Initialize database**:
   ```bash
   python create_db.py
   ```

7. **Create required directories**:
   ```bash
   mkdir -p uploads vectorstores
   ```

## Usage

1. **Start the application**:
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --host localhost --port 8000 --reload
   ```

2. **Access the application**:
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Using the application**:
   - Sign up for a new account or log in
   - Upload documents (PDF, DOCX, or TXT)
   - Start chat sessions to ask questions about your documents
   - Generate summaries of your documents
   - Access previous chat sessions from the sidebar

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Create new user account
- `POST /api/auth/login` - Authenticate user
- `POST /api/auth/web/login` - Web-based login
- `POST /api/auth/web/signup` - Web-based signup
- `POST /api/auth/logout` - Logout user

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/` - Get user's documents
- `GET /api/documents/{document_id}` - Get document details
- `POST /api/documents/{document_id}/summarize` - Generate summary

### Chat
- `POST /api/chat/start` - Start new chat session
- `POST /api/chat/chat` - Send message in chat
- `GET /api/chat/sessions` - Get user's chat sessions

### Web Routes
- `GET /` - Home page
- `GET /login` - Login page
- `GET /signup` - Signup page
- `GET /dashboard` - User dashboard
- `GET /document/{document_id}` - Document detail page
- `GET /chat/{session_id}` - Chat session page

## Project Structure

```
chatscribe2/
├── app/
│   ├── api/                 # API route handlers
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── chat.py         # Chat endpoints
│   │   ├── documents.py    # Document endpoints
│   │   ├── web.py          # Web page routes
│   │   └── deps.py         # Dependencies
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration settings
│   │   ├── database.py     # Database connection
│   │   ├── security.py     # Authentication utilities
│   │   ├── ai_service.py   # AI/ML service
│   │   └── file_processor.py # File processing
│   ├── crud/               # Database operations
│   │   └── crud.py         # CRUD functions
│   ├── models/             # Database models
│   │   └── models.py       # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   │   └── schemas.py      # API schemas
│   ├── static/             # Static files
│   │   ├── css/           # Stylesheets
│   │   └── js/            # JavaScript
│   ├── templates/          # HTML templates
│   │   ├── base.html      # Base template
│   │   ├── home.html      # Landing page
│   │   ├── login.html     # Login page
│   │   ├── signup.html    # Signup page
│   │   ├── dashboard.html # User dashboard
│   │   ├── document.html  # Document page
│   │   ├── chat.html      # Chat interface
│   │   └── error.html     # Error page
│   └── main.py             # FastAPI application
├── uploads/                # Uploaded files
├── vectorstores/          # AI vector databases
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── create_db.py          # Database initialization
├── main.py               # Application entry point
└── README.md             # This file
```

## Security Features

- JWT-based authentication with secure cookie storage
- Password hashing using bcrypt
- File type validation and size limits
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for cross-origin requests
- Environment-based configuration management

## Configuration

Key configuration options in `.env`:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (use a strong, random key)
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration time
- `MAX_FILE_SIZE`: Maximum upload file size in bytes
- `DEBUG`: Enable debug mode for development

## Development

To run in development mode:

```bash
export DEBUG=True
python main.py
```

This enables auto-reload and debug logging.

## Production Deployment

1. Set `DEBUG=False` in production
2. Use a strong, unique `SECRET_KEY`
3. Configure HTTPS and set `secure=True` for cookies
4. Use a production WSGI server like Gunicorn
5. Set up reverse proxy with Nginx
6. Configure proper database connection pooling
7. Set up monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on the GitHub repository or contact the development team.
