"""FastAPI routes for image uploads."""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.analysis import BLUR_THRESHOLD, LOW_LIGHT_THRESHOLD
from app.background import process_image
from app.config import UPLOAD_DIR
from app.database import get_db
from app.models import Image
from app.schemas import ResultResponse, StatusResponse, UploadResponse
from app.utils import get_image_extension, save_uploaded_image, validate_image_content_type

# All upload endpoints share this router, mounted directly on the app in main.py.
router = APIRouter(tags=["Images"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Accept a vehicle image upload and persist it with a pending status.

    Steps:
    1. Validate the file extension (must be .jpg, .jpeg, or .png).
    2. Validate the declared MIME type (must be image/jpeg or image/png).
    3. Generate a UUID filename so the stored file name is globally unique.
    4. Stream the file to disk inside the uploads/ directory while checking
       the file signature (magic bytes) and enforcing the configured size cap.
    5. Insert a row into the images table with status="pending".
    6. Commit the transaction and return {"id": ..., "status": "pending"}.

    If the database write fails the uploaded file is cleaned up so the
    filesystem stays consistent with the database.
    """
    filepath: Path | None = None
    try:
        # Step 1 & 2: file type checks before touching the filesystem
        extension = get_image_extension(file.filename)
        validate_image_content_type(file.content_type)

        # Step 3: UUID filename — the original name is preserved in the DB
        filepath = Path(UPLOAD_DIR) / f"{uuid4()}{extension}"

        # Step 4: write the file and verify magic bytes + size
        await save_uploaded_image(file, filepath)

        # Step 5: insert metadata row; status defaults to "pending" in the model
        image = Image(
            filename=file.filename or filepath.name,
            filepath=filepath.resolve().as_posix(),
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        background_tasks.add_task(process_image, image.id)

        # Step 6: return exactly the required shape
        return UploadResponse(id=image.id, status=image.status)

    except SQLAlchemyError as error:
        db.rollback()
        if filepath is not None:
            filepath.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save image metadata to the database.",
        ) from error
    finally:
        await file.close()


@router.get("/images/{image_id}/status", response_model=StatusResponse)
def get_image_status(image_id: int, db: Session = Depends(get_db)) -> StatusResponse:
    """Return the current processing status for an uploaded image."""
    image = db.get(Image, image_id)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    analysis = image.analysis_result
    return StatusResponse(
        id=image.id,
        filename=image.filename,
        status=image.status,
        created_at=image.created_at,
        updated_at=analysis.completed_at if analysis is not None else None,
    )


@router.get("/images/{image_id}/result", response_model=ResultResponse)
def get_image_result(image_id: int, db: Session = Depends(get_db)) -> ResultResponse:
    """Return the stored analysis result for an uploaded image."""
    image = db.get(Image, image_id)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    if image.analysis_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result is not available yet.",
        )

    result = image.analysis_result
    return ResultResponse(
        id=result.id,
        image_id=result.image_id,
        blur_score=result.blur_score,
        is_blurry=(result.blur_score < BLUR_THRESHOLD)
        if result.blur_score is not None
        else None,
        brightness_score=result.brightness_score,
        low_light=(result.brightness_score < LOW_LIGHT_THRESHOLD)
        if result.brightness_score is not None
        else None,
        plate_text=result.plate_text,
        extracted_text=result.extracted_text,
        plate_valid=result.plate_valid,
        duplicate=result.duplicate,
        remarks=result.remarks,
        completed_at=result.completed_at,
    )
