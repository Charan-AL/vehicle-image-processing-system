"""
SQLAlchemy ORM models for database tables.

Models:
- Image: Stores uploaded vehicle image metadata
- AnalysisResult: Stores image analysis results (blur, brightness, plate detection, etc.)
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

# ============================================================================
# TABLE 1: IMAGE
# ============================================================================
class Image(Base):
    """
    Image model - stores metadata for uploaded vehicle images.

    Relationship:
    - One Image can have ONE AnalysisResult (or none if not processed yet)
    """

    __tablename__ = "images"

    # Primary key - auto-incrementing unique identifier
    id = Column(Integer, primary_key=True, index=True)

    # Original filename when uploaded (e.g., "car_001.jpg")
    filename = Column(String(255), nullable=False)

    # Full file path where image is stored (e.g., "uploads/car_001.jpg")
    filepath = Column(String(500), nullable=False, unique=True)

    # Status of image processing
    # Possible values: "pending", "processing", "completed", "failed"
    status = Column(String(50), nullable=False, default="pending", index=True)

    # Timestamp when image was uploaded
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationship to AnalysisResult
    # One image can have one analysis result
    analysis_result = relationship("AnalysisResult", uselist=False, back_populates="image")


# ============================================================================
# TABLE 2: ANALYSISRESULT
# ============================================================================
class AnalysisResult(Base):
    """
    AnalysisResult model - stores analysis results for vehicle images.

    Contains:
    - Image quality metrics (blur, brightness)
    - License plate detection (text, validity)
    - Data quality flags (duplicates)

    Relationship:
    - Many AnalysisResults belong to ONE Image (but currently one per image)
    """

    __tablename__ = "analysis_results"

    # Primary key - auto-incrementing unique identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key - references Image.id (which image this result belongs to)
    # On delete cascade: if image is deleted, result is deleted too
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True)

    # Image quality metric (0-1 scale, 0=very blurry, 1=sharp)
    # Calculated using OpenCV edge detection
    blur_score = Column(Float, nullable=True)

    # Image brightness metric (0-1 scale, 0=dark, 1=bright)
    # Calculated from pixel intensity averages
    brightness_score = Column(Float, nullable=True)

    # Normalized registration number detected in the image
    plate_text = Column(Text, nullable=True)

    # Raw text extracted from the image by OCR
    extracted_text = Column(Text, nullable=True)

    # Whether detected plate text is valid
    # True: valid format, False: invalid/unrecognized format
    plate_valid = Column(Boolean, nullable=True, default=False)

    # Whether image is flagged as duplicate
    # True: similar image already processed, False: unique image
    duplicate = Column(Boolean, nullable=True, default=False)

    # Additional remarks or notes about the analysis
    # Examples: "Low quality", "Multiple plates detected", "No plate found"
    remarks = Column(String(500), nullable=True)

    # Timestamp when analysis was completed
    # Set when processing finishes (success or failure)
    completed_at = Column(DateTime, nullable=True, index=True)

    # Relationship back to Image
    # Allows accessing parent image: result.image.filename
    image = relationship("Image", back_populates="analysis_result")
