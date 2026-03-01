from __future__ import annotations
import os, uuid
from django.conf import settings
from claims.utils.image_utils import prepare_image_for_upload, is_image

TMP_DIR = os.path.join(settings.BASE_DIR, "tmp")


def save_uploaded_file(file) -> tuple[uuid.UUID, str, str, str]:
    """
    Saves an uploaded Django file object to tmp/.
    Converts images to JPEG if not natively supported.

    Returns: (actual_uuid, final_filename, final_mime, final_path)
    """
    os.makedirs(TMP_DIR, exist_ok=True)

    file_uuid     = uuid.uuid4()
    original_path = os.path.join(TMP_DIR, str(file_uuid))
    original_mime = file.content_type or "application/octet-stream"

    # Save original to disk
    with open(original_path, "wb") as f:
        for chunk in file.chunks():
            f.write(chunk)

    final_path     = original_path
    final_mime     = original_mime
    final_filename = file.name

    # Convert unsupported images to JPEG
    if is_image(original_mime):
        final_path, final_mime = prepare_image_for_upload(
            src_path=original_path,
            mime=original_mime,
            tmp_dir=TMP_DIR,
            base_filename=str(file_uuid),
        )
        if final_mime == "image/jpeg" and original_mime != "image/jpeg":
            name_without_ext = os.path.splitext(file.name)[0]
            final_filename   = f"{name_without_ext}.jpg"

    # If converted, store under a new UUID
    actual_uuid = file_uuid
    if final_path != original_path:
        converted_uuid = uuid.uuid4()
        converted_path = os.path.join(TMP_DIR, str(converted_uuid))
        os.rename(final_path, converted_path)
        actual_uuid = converted_uuid

    return actual_uuid, final_filename, final_mime, final_path