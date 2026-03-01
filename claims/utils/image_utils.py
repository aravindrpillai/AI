from __future__ import annotations
import os


# Formats Claude natively supports — no conversion needed
CLAUDE_NATIVE_IMAGE_MIMES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
}

# Any image mime that is NOT in the above set will be converted to JPEG
def is_image(mime: str) -> bool:
    return (mime or "").lower().startswith("image/")


def needs_conversion(mime: str) -> bool:
    return is_image(mime) and mime.lower() not in CLAUDE_NATIVE_IMAGE_MIMES


def convert_to_jpeg(src_path: str, dest_path: str) -> bool:
    """
    Convert any image format to JPEG.
    Tries pillow_heif first (for HEIC), then falls back to Pillow alone.
    Returns True if conversion succeeded.
    """
    try:
        from PIL import Image

        # Register HEIC/HEIF opener if available
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            pass  # Not installed — fine for non-HEIC formats

        img = Image.open(src_path)
        img.convert("RGB").save(dest_path, format="JPEG", quality=90)
        return True

    except Exception as e:
        print(f"[ImageUtils] Conversion failed for {src_path}: {e}")
        return False


def prepare_image_for_upload(
    src_path: str,
    mime: str,
    tmp_dir: str,
    base_filename: str,
) -> tuple[str, str]:
    """
    If the image needs conversion, convert it to JPEG and return the new path + mime.
    If already supported, return the original path + mime unchanged.

    Returns: (final_path, final_mime)
    """
    if not needs_conversion(mime):
        return src_path, mime

    jpeg_filename = f"{base_filename}_converted.jpg"
    jpeg_path = os.path.join(tmp_dir, jpeg_filename)

    success = convert_to_jpeg(src_path, jpeg_path)
    if success:
        print(f"[ImageUtils] Converted {mime} → image/jpeg: {jpeg_path}")
        return jpeg_path, "image/jpeg"

    # Conversion failed — return original and let Claude handle/skip it
    print(f"[ImageUtils] Conversion failed, using original: {src_path}")
    return src_path, mime