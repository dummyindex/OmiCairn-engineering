"""
Utility functions for close_out_app.
"""
import os
from PIL import Image


def get_image_extension(file_path):
    """
    Get the actual image format extension from file content.
    Returns extension without dot (e.g., 'jpg', 'png').
    """
    with Image.open(file_path) as img:
        fmt = img.format.lower()
        if fmt == 'jpeg':
            return 'jpg'
        return fmt


def fix_image_extension(file_path):
    """
    Fix image extension if missing.
    Returns the corrected file path.
    """
    if '.' in os.path.basename(file_path):
        return file_path
    ext = get_image_extension(file_path)
    if ext == 'jpg':
        ext = 'jpeg'
    new_file_path = file_path + '.' + ext
    if new_file_path != file_path:
        os.rename(file_path, new_file_path)
        print(f"Renamed {file_path} to {new_file_path}")
    return new_file_path


def generate_thumbnail(image_path: str, thumbnail_path: str, max_side_length=128):
    """
    Generate thumbnail for image files (PNG, JPG, TIFF) and PDF.
    Thumbnail format matches the original file format.

    Args:
        image_path: Path to the original image
        thumbnail_path: Path to save the thumbnail
        max_side_length: Maximum side length for thumbnail (default: 128)
    """
    try:
        _, ext = os.path.splitext(image_path)
        ext_lower = ext.lower()

        # Handle PDF files
        if ext_lower == '.pdf':
            try:
                import fitz  # PyMuPDF
                pdf_document = fitz.open(image_path)
                first_page = pdf_document[0]
                page_rect = first_page.rect
                width, height = page_rect.width, page_rect.height

                if width >= height:
                    zoom = max_side_length / width
                else:
                    zoom = max_side_length / height

                mat = fitz.Matrix(zoom, zoom)
                pix = first_page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(thumbnail_path, "PDF")
                pdf_document.close()
                print(f"Generated PDF thumbnail: {thumbnail_path}")
            except ImportError:
                print("PyMuPDF (fitz) not installed, falling back to pdf2image")
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(image_path, first_page=1, last_page=1)
                    if images:
                        img = images[0]
                        width, height = img.size
                        if width >= height:
                            new_width = max_side_length
                            new_height = int(height * max_side_length / width)
                        else:
                            new_height = max_side_length
                            new_width = int(width * max_side_length / height)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                        img.save(thumbnail_path, "PDF")
                        print(f"Generated PDF thumbnail using pdf2image: {thumbnail_path}")
                except ImportError:
                    print("Neither PyMuPDF nor pdf2image is installed. Cannot process PDF files.")
                    raise
            except Exception as e:
                print(f"Error processing PDF file {image_path}: {e}")
                raise
        else:
            # Handle regular image formats (PNG, JPG, TIFF, etc.)
            with Image.open(image_path) as img:
                original_format = img.format
                width, height = img.size

                if width <= 0 or height <= 0:
                    raise ValueError(f"Invalid image dimensions: {width}x{height}")

                # If image is already small enough, just copy it
                if width <= max_side_length and height <= max_side_length:
                    print(f"Image already small enough ({width}x{height}), copying directly")
                    if original_format:
                        img.save(thumbnail_path, format=original_format)
                    else:
                        img.save(thumbnail_path)
                    return

                # Convert RGBA to RGB if saving as JPEG
                if original_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img

                # Calculate new dimensions
                if width >= height:
                    new_width = max_side_length
                    new_height = int(height * max_side_length / width)
                else:
                    new_height = max_side_length
                    new_width = int(width * max_side_length / height)

                new_width = max(1, new_width)
                new_height = max(1, new_height)

                # Resize with high-quality resampling
                try:
                    resample_method = Image.LANCZOS
                except AttributeError:
                    resample_method = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.BICUBIC

                img = img.resize((new_width, new_height), resample_method)

                if original_format:
                    img.save(thumbnail_path, format=original_format)
                    print(f"Generated {original_format} thumbnail: {thumbnail_path} ({new_width}x{new_height})")
                else:
                    img.save(thumbnail_path)
                    print(f"Generated thumbnail: {thumbnail_path} ({new_width}x{new_height})")

    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        raise
