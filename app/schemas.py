"""
Pydantic schemas for request and response validation.

Schemas:
- UploadResponse: Response when image is uploaded
- StatusResponse: Response when checking image status
- ResultResponse: Response with analysis results
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

# ============================================================================
# RESPONSE SCHEMA 1: UploadResponse
# ============================================================================
class UploadResponse(BaseModel):
    """
    Response schema for image upload endpoint.

    Returns details of the uploaded image and initial processing status.
    When user uploads an image, API responds with this schema.

    Example:
    {
        "id": 1,
        "filename": "car_001.jpg",
        "filepath": "uploads/car_001.jpg",
        "status": "pending",
        "message": "Image uploaded successfully. Processing started.",
        "created_at": "2024-01-15T10:30:00"
    }
    """

    # Image ID from database (assigned by database on creation)
    id: int = Field(
        description="Unique image ID assigned by database",
        example=1
    )

    # Original filename uploaded by user
    filename: str = Field(
        description="Original filename when uploaded",
        example="car_001.jpg"
    )

    # Full path where image is stored
    filepath: str = Field(
        description="Full file path where image is stored",
        example="uploads/car_001.jpg"
    )

    # Current processing status
    # Always "pending" immediately after upload
    status: str = Field(
        description="Current processing status: pending, processing, completed, failed",
        example="pending"
    )

    # User-friendly message about what happened
    message: str = Field(
        description="Message describing the upload result",
        example="Image uploaded successfully. Processing started."
    )

    # When the image was created/uploaded
    created_at: datetime = Field(
        description="Timestamp when image was uploaded",
        example="2024-01-15T10:30:00"
    )

    # Configuration: model_config tells Pydantic to handle ORM models
    # This allows schema to work with SQLAlchemy model instances
    model_config = {
        "from_attributes": True,  # Can be constructed from SQLAlchemy models
        "json_schema_extra": {
            "example": {
                "id": 1,
                "filename": "car_001.jpg",
                "filepath": "uploads/car_001.jpg",
                "status": "pending",
                "message": "Image uploaded successfully. Processing started.",
                "created_at": "2024-01-15T10:30:00"
            }
        }
    }


# ============================================================================
# RESPONSE SCHEMA 2: StatusResponse
# ============================================================================
class StatusResponse(BaseModel):
    """
    Response schema for checking image processing status.

    Returns current processing status of an image.
    Useful for checking if image is still processing or completed.

    Example:
    {
        "id": 1,
        "filename": "car_001.jpg",
        "status": "completed",
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:31:45"
    }
    """

    # Image ID (primary key)
    id: int = Field(
        description="Unique image ID",
        example=1
    )

    # Original filename
    filename: str = Field(
        description="Original filename when uploaded",
        example="car_001.jpg"
    )

    # Current processing status
    # Possible values: "pending", "processing", "completed", "failed"
    status: str = Field(
        description="Current processing status",
        example="completed"
    )

    # When image was uploaded
    created_at: datetime = Field(
        description="Timestamp when image was uploaded",
        example="2024-01-15T10:30:00"
    )

    # When processing was last updated
    # Used to show when analysis was completed
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when status was last updated",
        example="2024-01-15T10:31:45"
    )

    # Configuration: Allow construction from SQLAlchemy models
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "filename": "car_001.jpg",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:31:45"
            }
        }
    }


# ============================================================================
# RESPONSE SCHEMA 3: ResultResponse
# ============================================================================
class ResultResponse(BaseModel):
    """
    Response schema for image analysis results.

    Returns complete analysis results including quality metrics and plate detection.
    Only populated after image processing is completed.

    Example:
    {
        "id": 1,
        "image_id": 1,
        "blur_score": 0.87,
        "brightness_score": 0.72,
        "plate_text": "MH02AB1234",
        "plate_valid": true,
        "duplicate": false,
        "remarks": "Valid plate detected successfully",
        "completed_at": "2024-01-15T10:31:45"
    }
    """

    # Result ID (primary key)
    id: int = Field(
        description="Unique analysis result ID",
        example=1
    )

    # Reference to the image this result belongs to
    image_id: int = Field(
        description="ID of the image being analyzed",
        example=1
    )

    # Blur quality metric (0.0 to 1.0)
    # 0.0 = very blurry (bad), 1.0 = sharp (good)
    # Calculated using OpenCV edge detection
    blur_score: Optional[float] = Field(
        default=None,
        description="Blur quality metric (0.0=blurry, 1.0=sharp)",
        example=0.87
    )

    # Brightness quality metric (0.0 to 1.0)
    # 0.0 = too dark (underexposed), 1.0 = too bright (overexposed)
    # Optimal is around 0.5-0.7
    brightness_score: Optional[float] = Field(
        default=None,
        description="Brightness metric (0.0=dark, 1.0=bright)",
        example=0.72
    )

    # License plate text extracted by OCR
    # Result from EasyOCR model
    # May be None if no plate detected
    plate_text: Optional[str] = Field(
        default=None,
        description="Extracted license plate text from OCR",
        example="MH02AB1234"
    )

    # Whether the detected plate text is valid
    # True = matches expected license plate format
    # False = invalid format or unparseable
    plate_valid: Optional[bool] = Field(
        default=None,
        description="Whether plate text is valid format",
        example=True
    )

    # Whether image is flagged as duplicate
    # True = similar image already in database
    # False = new/unique image
    duplicate: Optional[bool] = Field(
        default=None,
        description="Whether image is a duplicate",
        example=False
    )

    # Additional notes or remarks about the analysis
    # Human-readable text explaining the results
    # Examples: "Valid plate", "Low quality", "No plate found", "Processing error"
    remarks: Optional[str] = Field(
        default=None,
        description="Notes about the analysis",
        example="Valid plate detected successfully"
    )

    # When the analysis was completed
    # Set after processing finishes (success or failure)
    # None = still processing
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when analysis was completed",
        example="2024-01-15T10:31:45"
    )

    # Configuration: Allow construction from SQLAlchemy models
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "image_id": 1,
                "blur_score": 0.87,
                "brightness_score": 0.72,
                "plate_text": "MH02AB1234",
                "plate_valid": True,
                "duplicate": False,
                "remarks": "Valid plate detected successfully",
                "completed_at": "2024-01-15T10:31:45"
            }
        }
    }


# ============================================================================
# COMBINED RESPONSE SCHEMA: ImageDetailResponse
# ============================================================================
class ImageDetailResponse(BaseModel):
    """
    Combined response schema for image with its analysis results.

    Combines Image data with its AnalysisResult data.
    Used when client needs both image info and analysis results.

    Example:
    {
        "image": {
            "id": 1,
            "filename": "car_001.jpg",
            "filepath": "uploads/car_001.jpg",
            "status": "completed",
            "created_at": "2024-01-15T10:30:00"
        },
        "analysis": {
            "id": 1,
            "image_id": 1,
            "blur_score": 0.87,
            "brightness_score": 0.72,
            "plate_text": "MH02AB1234",
            "plate_valid": true,
            "duplicate": false,
            "remarks": "Valid plate detected",
            "completed_at": "2024-01-15T10:31:45"
        }
    }
    """

    # Image metadata
    # Contains: id, filename, status, timestamps
    image: dict = Field(
        description="Image metadata from images table",
        example={
            "id": 1,
            "filename": "car_001.jpg",
            "filepath": "uploads/car_001.jpg",
            "status": "completed",
            "created_at": "2024-01-15T10:30:00"
        }
    )

    # Analysis results
    # Contains: blur_score, brightness_score, plate_text, etc.
    # Can be None if image hasn't been analyzed yet
    analysis: Optional[dict] = Field(
        default=None,
        description="Analysis results from analysis_results table",
        example={
            "id": 1,
            "image_id": 1,
            "blur_score": 0.87,
            "brightness_score": 0.72,
            "plate_text": "MH02AB1234",
            "plate_valid": True,
            "duplicate": False,
            "remarks": "Valid plate detected",
            "completed_at": "2024-01-15T10:31:45"
        }
    )

    # Configuration: Allow construction from SQLAlchemy models
    model_config = {
        "from_attributes": True
    }
