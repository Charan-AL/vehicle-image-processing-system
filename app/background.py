"""Background task management for asynchronous image processing."""

import concurrent.futures
import logging
from datetime import datetime

from app.analysis import analyze_image
from app.config import PROCESSING_TIMEOUT_SECONDS
from app.database import SessionLocal
from app.models import AnalysisResult, Image

logger = logging.getLogger(__name__)

# Shared executor so every background task runs in a dedicated thread that can
# be timed out without blocking the event loop.
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr-worker")


def _mark_failed(image_id: int, reason: str) -> None:
    """Persist a failed status for the given image without raising."""
    db = SessionLocal()
    try:
        image = db.get(Image, image_id)
        if image is None:
            return
        result = image.analysis_result
        if result is None:
            result = AnalysisResult(image_id=image_id)
            db.add(result)
        result.plate_text = None
        result.extracted_text = None
        result.plate_valid = None
        result.duplicate = None
        result.remarks = reason
        result.completed_at = datetime.utcnow()
        image.status = "failed"
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Unable to record processing failure for image %s.", image_id)
    finally:
        db.close()


def _run_analysis(filepath: str) -> dict:
    """Execute analysis in a thread (so it can be cancelled via future timeout)."""
    return analyze_image(filepath)


def process_image(image_id: int) -> None:
    """Process an uploaded image and persist its lifecycle state.

    The heavy OCR work is executed inside a thread-pool future so a wall-clock
    timeout can be enforced without blocking the uvicorn event loop.
    """
    db = SessionLocal()
    filepath: str | None = None
    try:
        image = db.get(Image, image_id)
        if image is None:
            logger.warning("Image %s was not found for background processing.", image_id)
            return

        filepath = image.filepath
        image.status = "processing"
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not mark image %s as processing.", image_id)
        return
    finally:
        db.close()

    # Run the heavy OCR work with a hard timeout so a hung EasyOCR call does
    # not leave the row in "processing" forever.
    future = _executor.submit(_run_analysis, filepath)
    try:
        analysis = future.result(timeout=PROCESSING_TIMEOUT_SECONDS)
    except concurrent.futures.TimeoutError:
        future.cancel()
        logger.error(
            "Processing timed out after %ds for image %s.",
            PROCESSING_TIMEOUT_SECONDS,
            image_id,
        )
        _mark_failed(image_id, f"Processing timed out after {PROCESSING_TIMEOUT_SECONDS}s.")
        return
    except Exception:
        logger.exception("Analysis raised an exception for image %s.", image_id)
        _mark_failed(image_id, "Processing failed. Check the server logs for details.")
        return

    db = SessionLocal()
    try:
        image = db.get(Image, image_id)
        if image is None:
            logger.warning("Image %s disappeared before results could be saved.", image_id)
            return

        result = image.analysis_result
        if result is None:
            result = AnalysisResult(image_id=image.id)
            db.add(result)

        result.blur_score = analysis.get("blur_score")
        result.brightness_score = analysis.get("brightness_score")
        result.plate_text = analysis.get("plate_text")
        result.extracted_text = analysis.get("extracted_text")
        result.plate_valid = analysis.get("plate_valid")
        result.duplicate = analysis.get("duplicate")
        result.remarks = analysis.get("remarks")
        result.completed_at = datetime.utcnow()
        image.status = "completed"
        db.commit()
        logger.info("Image %s completed successfully.", image_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to persist results for image %s.", image_id)
        _mark_failed(image_id, "Failed to save results. Check the server logs for details.")
    finally:
        db.close()


def recover_stale_processing_jobs() -> None:
    """On startup, mark any rows stuck in 'processing' as failed.

    These are jobs that were in-flight when the previous process exited
    (container restart, OOM, SIGKILL, etc.).  They will never self-resolve,
    so we surface them as failed so operators can re-submit.
    """
    db = SessionLocal()
    try:
        stale = db.query(Image).filter(Image.status == "processing").all()
        if not stale:
            return
        for image in stale:
            result = image.analysis_result
            if result is None:
                result = AnalysisResult(image_id=image.id)
                db.add(result)
            if not result.remarks:
                result.remarks = "Processing interrupted by server restart."
            result.completed_at = datetime.utcnow()
            image.status = "failed"
        db.commit()
        logger.warning(
            "Recovered %d stale processing job(s) on startup.", len(stale)
        )
    except Exception:
        db.rollback()
        logger.exception("Could not recover stale processing jobs on startup.")
    finally:
        db.close()
