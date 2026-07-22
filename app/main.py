"""
FastAPI application entry point.
Initializes the FastAPI app with middleware, routers, and configurations.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.background import recover_stale_processing_jobs
from app.database import engine, initialize_database
from app.routes import router

# Initialize FastAPI app
app = FastAPI(
    title="Vehicle Image Processing System",
    description="API for processing vehicle images and extracting license plate information",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc UI
    openapi_url="/api/openapi.json"  # OpenAPI schema
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def migrate_database() -> None:
    initialize_database()
    recover_stale_processing_jobs()


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Check if the API and database are ready."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready.",
        ) from error

    return {"status": "ok", "message": "Vehicle Image Processing API is running"}

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Vehicle Image Processing System",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
