from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from frame2file.core.image_loader import create_thumbnail_bytes, find_images
from frame2file.core.pdf_exporter import export_images_to_pdf


class FolderScanWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, folder: Path) -> None:
        super().__init__()
        self.folder = folder

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(find_images(self.folder))
        except Exception as exc:
            self.failed.emit(str(exc))


class ThumbnailWorker(QObject):
    thumbnail_ready = Signal(int, str, bytes, int, int)
    failed = Signal(int, str, str)
    finished = Signal()

    def __init__(self, images: list[Path], background_color: str) -> None:
        super().__init__()
        self.images = images
        self.background_color = background_color
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        for index, image_path in enumerate(self.images):
            if self._cancelled:
                break

            try:
                data, width, height = create_thumbnail_bytes(
                    image_path,
                    background_color=self.background_color,
                )
                self.thumbnail_ready.emit(index, str(image_path), data, width, height)
            except Exception as exc:
                self.failed.emit(index, str(image_path), str(exc))

        self.finished.emit()


class PdfExportWorker(QObject):
    progress = Signal(int, int, int)
    finished = Signal(str, int)
    failed = Signal(str)

    def __init__(self, images: list[Path], output_file: Path) -> None:
        super().__init__()
        self.images = images
        self.output_file = output_file

    @Slot()
    def run(self) -> None:
        try:
            export_images_to_pdf(
                self.images,
                self.output_file,
                progress_callback=lambda progress, current, total: self.progress.emit(
                    progress,
                    current,
                    total,
                ),
            )
            self.finished.emit(str(self.output_file), len(self.images))
        except Exception as exc:
            self.failed.emit(str(exc))

