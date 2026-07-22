# Vehicle Image Processing System

A FastAPI backend service combined with a Streamlit frontend for processing vehicle images and extracting license plate information using OCR (EasyOCR) and image analysis.

## Features

- **FastAPI Backend**: RESTful API for image upload and processing
- **Streamlit Frontend**: User-friendly interface for uploading and analyzing vehicle images
- **PostgreSQL Database**: Persistent storage for analysis results
- **Async Processing**: Background job processing for heavy computations
- **License Plate Recognition**: Automated license plate detection and OCR

## Project Structure

```
vehicle-image-processing-system/
├── app/                          # FastAPI backend
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration management
│   ├── database.py               # Database setup and utilities
│   ├── models.py                 # SQLAlchemy models
│   ├── schemas.py                # Pydantic schemas
│   ├── routes.py                 # API endpoints
│   ├── analysis.py               # Image analysis logic
│   ├── plate_validation.py       # License plate validation
│   ├── utils.py                  # Utility functions
│   └── background.py             # Background tasks
├── frontend/                     # Streamlit frontend
│   ├── app.py                    # Main Streamlit app
│   ├── api.py                    # API client for backend
│   ├── requirements.txt           # Frontend dependencies
│   └── Dockerfile                # Streamlit container
├── uploads/                      # Uploaded images directory
├── Dockerfile                    # Backend container
├── docker-compose.yml            # Docker Compose configuration
├── .dockerignore                 # Docker build ignore rules
├── requirements.txt              # Backend dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## Prerequisites

### Local Development
- Python 3.12+
- PostgreSQL 12+
- pip or conda

### Docker
- Docker 20.10+
- Docker Compose 2.0+

## Installation

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vehicle-image-processing-system
   ```

2. **Create virtual environment**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Frontend dependencies
   pip install -r frontend/requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration
   ```

5. **Initialize database**
   - Make sure PostgreSQL is running
   - Update `DATABASE_URL` in `.env`
   - The database schema will be created automatically on startup

### Running Locally (Without Docker)

**Terminal 1 - Backend**
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend**
```bash
cd frontend
streamlit run app.py
```

Access the application:
- **Frontend**: http://localhost:8501
- **Backend API Docs**: http://localhost:8000/api/docs
- **Backend ReDoc**: http://localhost:8000/api/redoc

## Docker Setup

### Build Docker Images

**Build all services**
```bash
docker-compose build
```

**Build individual services**
```bash
# Backend only
docker build -t vehicle-backend:latest .

# Frontend only
docker build -t vehicle-frontend:latest ./frontend
```

### Run with Docker Compose

**Start all services**
```bash
docker-compose up -d
```

**View logs**
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

**Stop all services**
```bash
docker-compose down
```

**Stop and remove volumes (clean state)**
```bash
docker-compose down -v
```

**Rebuild and restart**
```bash
docker-compose up -d --build
```

### Access Running Services

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Database**: localhost:5432

### Docker Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/vehicle_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=vehicle_db

# Backend
DEBUG=True
SQL_ECHO=False
UPLOAD_DIR=uploads

# Frontend
BACKEND_URL=http://backend:8000
```

**Note**: When using docker-compose, use `http://backend:8000` for `BACKEND_URL` (service name). Update this when deploying to production.

## Railway Deployment

### Prerequisites
- Railway account (https://railway.app)
- GitHub repository with the project code

### Deployment Steps

#### 1. Prepare Repository
- Ensure all Docker configuration files are committed:
  - `Dockerfile` (backend)
  - `frontend/Dockerfile`
  - `.dockerignore`
  - `frontend/.dockerignore`
  - `docker-compose.yml` (for reference)
  - `.env.example`
  - `requirements.txt`
  - `frontend/requirements.txt`

#### 2. Deploy PostgreSQL Service
1. Go to your Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Wait for PostgreSQL to be provisioned
4. Note the database connection details provided by Railway

#### 3. Deploy Backend Service
1. Click "New" → "GitHub Repo" or "Deploy from Repo"
2. Select your repository
3. Configure the service:
   - **Name**: vehicle-backend
   - **Root Directory**: `.` (root of repo)
   - **Dockerfile**: `Dockerfile`
   - **Port**: 8000
4. Set environment variables:
   - `DATABASE_URL`: Use reference to PostgreSQL service
     - In Railway, you can use: `${{DATABASE_URL}}`
     - Or manually copy the URL provided by PostgreSQL service
   - `DEBUG`: False (for production)
   - `SQL_ECHO`: False
   - `UPLOAD_DIR`: uploads
5. Deploy

#### 4. Deploy Frontend Service
1. Click "New" → "GitHub Repo" or "Deploy from Repo"
2. Select your repository
3. Configure the service:
   - **Name**: vehicle-frontend
   - **Root Directory**: `./frontend`
   - **Dockerfile**: `Dockerfile`
   - **Port**: 8501
4. Set environment variables:
   - `BACKEND_URL`: Point to your backend service
     - Example: `https://vehicle-backend.up.railway.app` (adjust with your actual backend URL)
     - In Railway, you can reference another service: `http://${{BACKEND_SERVICE_VARIABLE}}`
5. Deploy

### Railway Service Linking

To link the frontend to the backend dynamically:

1. In the **Frontend** service settings:
   - Add a reference to the Backend service
   - Use Railway's variable reference format: `${{BACKEND_URL}}`
   - Or manually set `BACKEND_URL` to the backend service's public URL

2. Make sure both services are deployed before linking

### Production Environment Variables

For Railway deployment, update these variables:

**Backend Service**:
```
DATABASE_URL=postgresql://user:password@host:port/database  # From PostgreSQL service
DEBUG=False
SQL_ECHO=False
UPLOAD_DIR=uploads
```

**Frontend Service**:
```
BACKEND_URL=https://vehicle-backend.up.railway.app  # Update with actual backend URL
```

### Monitoring and Logs

In Railway:
1. Select a service
2. Go to "Logs" tab to view real-time logs
3. Use "Deployments" tab to view deployment history
4. Check "Metrics" for CPU, memory, and network usage

### Scaling and Configuration

- **Backend Service**: Default allocation is usually sufficient; scale up if needed
- **Frontend Service**: Low resource requirements; default allocation is fine
- **PostgreSQL**: Default allocation usually sufficient for moderate use

### Health Checks

The services include health checks:
- **Backend**: `/health` endpoint
- **Frontend**: Streamlit health endpoint
- **Database**: PostgreSQL connection check

### Rollback

To rollback to a previous version in Railway:
1. Go to the service
2. Select "Deployments" tab
3. Choose the desired deployment
4. Click "Rollback"

## API Endpoints

### Health Check
```
GET /health
```
Returns service status.

### Root Endpoint
```
GET /
```
Returns API information.

### Upload Image
```
POST /upload
Content-Type: multipart/form-data

Body: file (image file)
```
Uploads an image for processing.

**Response**:
```json
{
  "id": "uuid",
  "status": "pending",
  "message": "Image received for processing"
}
```

### Get Status
```
GET /status/{processing_id}
```
Retrieves the current processing status.

### Get Result
```
GET /result/{processing_id}
```
Retrieves the completed analysis result.

## Configuration

### Backend Configuration (`app/config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:password@localhost:5432/vehicle_db` | PostgreSQL connection string |
| `DEBUG` | True | Enable debug mode |
| `SQL_ECHO` | False | Log SQL queries |
| `UPLOAD_DIR` | uploads | Directory for uploaded files |
| `MAX_UPLOAD_SIZE` | 10MB | Maximum file upload size |

### Frontend Configuration (`frontend/api.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `REQUEST_TIMEOUT` | 30s | Request timeout duration |
| `UPLOAD_TIMEOUT` | 180s | Upload request timeout |

## Troubleshooting

### Docker Issues

**Port already in use**
```bash
# Change port in docker-compose.yml or:
docker-compose down
# Kill process on the port
```

**Database connection error**
```bash
# Ensure PostgreSQL container is running
docker-compose logs postgres

# Rebuild and restart
docker-compose down -v
docker-compose up -d --build
```

**Frontend can't connect to backend**
- Check `BACKEND_URL` is set correctly
- Ensure both services are in the same network
- Verify backend is healthy: `docker-compose ps`

### Railway Issues

**Backend not connecting to database**
- Verify `DATABASE_URL` environment variable is set
- Check PostgreSQL service is running
- Review backend logs for connection errors

**Frontend can't reach backend**
- Verify `BACKEND_URL` points to the correct backend service
- Check both services are deployed and running
- Review CORS configuration in backend

**Deployment fails**
- Check logs in Railway dashboard
- Verify all required files are in repository
- Ensure Dockerfile paths are correct

## Performance Considerations

- **Image Processing**: Heavy operations (OCR, analysis) run asynchronously
- **Database**: Indexing on frequently queried columns
- **Uploads**: Large files stored in dedicated directory with size limits
- **Caching**: Results cached to avoid reprocessing

## Security Notes

- CORS is configured to allow all origins; adjust in production (`app/main.py`)
- Database credentials should be stored securely (use Railway PostgreSQL plugin)
- API endpoints should implement authentication/authorization as needed
- File uploads are validated by extension and MIME type
- Consider rate limiting for production deployment

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest test_plate_validation.py
```

### Code Style

The project follows standard Python conventions:
- Use type hints
- Follow PEP 8
- Use meaningful variable names

## License

[Add your license here]

## Support

For issues or questions:
1. Check this README
2. Review API documentation at `/api/docs`
3. Check application logs

## Quick Reference

### Common Commands

```bash
# Local development
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Docker local
docker-compose up -d
docker-compose logs -f
docker-compose down

# Railway deployment
# Push to GitHub → Railway auto-deploys
# Monitor in Railway dashboard
```

### Service URLs

| Service | Local | Docker | Railway |
|---------|-------|--------|---------|
| Frontend | http://localhost:8501 | http://localhost:8501 | https://vehicle-frontend.up.railway.app |
| Backend API | http://localhost:8000 | http://backend:8000 | https://vehicle-backend.up.railway.app |
| Backend Docs | http://localhost:8000/api/docs | http://backend:8000/api/docs | https://vehicle-backend.up.railway.app/api/docs |
| Database | localhost:5432 | postgres:5432 | Railway managed |
