from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageFile

from frame2file.core.sorting import natural_key

ImageFile.LOAD_TRUNCATED_IMAGES = True

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
THUMBNAIL_FILTER = getattr(Image, "Resampling", Image).LANCZOS


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def find_images(folder: Path) -> list[Path]:
    return sorted(
        [file for file in folder.iterdir() if is_supported_image(file)],
        key=natural_key,
    )


def filter_supported(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if path.suffix.lower() in SUPPORTED_EXTENSIONS]


def create_thumbnail_bytes(
    image_path: Path,
    size: tuple[int, int] = (198, 222),
    background_color: str = "#080d14",
) -> tuple[bytes, int, int]:
    """Create an RGB thumbnail buffer that the Qt layer can convert to QImage."""
    width, height = size
    with Image.open(image_path) as source:
        preview = source.copy()
        preview.thumbnail(size, THUMBNAIL_FILTER)

        background = Image.new("RGB", size, background_color)
        x = (width - preview.width) // 2
        y = (height - preview.height) // 2

        if preview.mode in ("RGBA", "LA") or (
            preview.mode == "P" and "transparency" in preview.info
        ):
            rgba = preview.convert("RGBA")
            background.paste(rgba, (x, y), rgba.getchannel("A"))
        else:
            background.paste(preview.convert("RGB"), (x, y))

        return background.tobytes("raw", "RGB"), width, height

