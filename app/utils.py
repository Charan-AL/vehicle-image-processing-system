"""Utilities for validating and storing uploaded images."""

from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_IMAGE_MIME_TYPES, MAX_UPLOAD_SIZE

JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def get_image_extension(filename: str | None) -> str:
    """Return a normalized, permitted extension from an uploaded filename."""
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPG, JPEG, and PNG images are accepted.",
        )
    return extension


def validate_image_content_type(content_type: str | None) -> None:
    """Reject uploads whose declared media type is not a supported image type."""
    if content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only image/jpeg and image/png uploads are accepted.",
        )


def has_valid_image_signature(content: bytes) -> bool:
    """Check whether file content begins with a JPEG or PNG signature."""
    return content.startswith(JPEG_SIGNATURE) or content.startswith(PNG_SIGNATURE)


async def save_uploaded_image(upload: UploadFile, destination: Path) -> None:
    """Stream a validated upload to disk while enforcing the configured size limit."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    first_chunk = True

    try:
        with destination.open("xb") as output_file:
            while chunk := await upload.read(1024 * 1024):
                if first_chunk:
                    first_chunk = False
                    if not has_valid_image_signature(chunk):
                        raise HTTPException(
                            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail="The uploaded file is not a valid JPG, JPEG, or PNG image.",
                        )

                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Image size must not exceed {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
                    )

                output_file.write(chunk)

        if bytes_written == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded image is empty.",
            )
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
