"""Background task management for asynchronous image processing."""

import logging
from datetime import datetime

from app.analysis import analyze_image
from app.database import SessionLocal
from app.models import AnalysisResult, Image

logger = logging.getLogger(__name__)


def process_image(image_id: int) -> None:
    """Process an uploaded image and persist its lifecycle state."""
    db = SessionLocal()
    try:
        image = db.get(Image, image_id)
        if image is None:
            logger.warning("Image %s was not found for background processing.", image_id)
            return

        image.status = "processing"
        db.commit()

        analysis = analyze_image(image.filepath)
        result = image.analysis_result
        if result is None:
            result = AnalysisResult(image_id=image.id)
            db.add(result)

        result.blur_score = analysis.get("blur_score")
        result.brightness_score = analysis.get("brightness_score")
        result.plate_text = analysis.get("plate_text")
        result.plate_valid = analysis.get("plate_valid")
        result.duplicate = analysis.get("duplicate")
        result.remarks = analysis.get("remarks")
        result.completed_at = datetime.utcnow()
        image.status = "completed"
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Background processing failed for image %s.", image_id)
        try:
            image = db.get(Image, image_id)
            if image is not None:
                result = image.analysis_result
                if result is None:
                    result = AnalysisResult(image_id=image.id)
                    db.add(result)
                result.plate_text = None
                result.plate_valid = None
                result.duplicate = None
                result.remarks = "Processing failed. Check the server logs for details."
                result.completed_at = datetime.utcnow()
                image.status = "failed"
                db.commit()
        except Exception:
            db.rollback()
            logger.exception("Unable to record processing failure for image %s.", image_id)
    finally:
        db.close()
