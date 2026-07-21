"""
FastAPI application entry point.
Initializes the FastAPI app with middleware, routers, and configurations.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import ensure_analysis_result_schema
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
    ensure_analysis_result_schema()


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Check if the API is running."""
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
