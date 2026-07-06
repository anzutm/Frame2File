from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image

ProgressCallback = Callable[[int, int, int], None]


def export_images_to_pdf(
    images: list[Path],
    output_file: Path,
    progress_callback: ProgressCallback | None = None,
) -> None:
    """Export images to one PDF using Frame2File's original export behavior."""
    if not images:
        raise ValueError("Tidak ada gambar untuk dibuat menjadi PDF.")

    pages: list[Image.Image] = []

    try:
        for index, image_path in enumerate(images, start=1):
            with Image.open(image_path) as source:
                if source.mode in ("RGBA", "LA") or (
                    source.mode == "P" and "transparency" in source.info
                ):
                    background = Image.new("RGB", source.size, "white")
                    rgba = source.convert("RGBA")
                    background.paste(rgba, mask=rgba.getchannel("A"))
                    page = background
                else:
                    page = source.convert("RGB")

                pages.append(page.copy())

            if progress_callback is not None:
                progress = int(index / len(images) * 100)
                progress_callback(progress, index, len(images))

        output_file.parent.mkdir(parents=True, exist_ok=True)
        pages[0].save(
            output_file,
            "PDF",
            save_all=True,
            append_images=pages[1:],
            resolution=150.0,
        )
    finally:
        for page in pages:
            page.close()
