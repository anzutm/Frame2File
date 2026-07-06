from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from frame2file.core.image_loader import SUPPORTED_EXTENSIONS, filter_supported
from frame2file.gui.resources.theme import PALETTE
from frame2file.gui.services.workers import FolderScanWorker, PdfExportWorker, ThumbnailWorker
from frame2file.gui.widgets.thumbnail_list import ThumbnailListWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Frame2File")
        self.resize(1180, 860)
        self.setMinimumSize(920, 720)

        self.folder_path: Path | None = None
        self._scan_thread: QThread | None = None
        self._scan_worker: FolderScanWorker | None = None
        self._thumbnail_thread: QThread | None = None
        self._thumbnail_worker: ThumbnailWorker | None = None
        self._export_thread: QThread | None = None
        self._export_worker: PdfExportWorker | None = None

        self._build_ui()
        self._connect_signals()
        self._set_status("Pilih folder gambar untuk memulai.")

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._enable_dark_title_bar()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._cancel_thumbnail_worker()
        super().closeEvent(event)

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(34, 26, 34, 24)
        root.setSpacing(18)

        root.addLayout(self._build_header())
        root.addWidget(self._build_folder_panel())
        root.addWidget(self._build_preview_panel(), 1)
        root.addWidget(self._build_progress_panel())

        self.export_button = QPushButton("Buat PDF")
        self.export_button.setObjectName("ExportButton")
        self.export_button.setMinimumHeight(58)
        root.addWidget(self.export_button)

        self.footer_label = QLabel(
            "Format didukung: JPG, JPEG, PNG, WEBP, BMP"
        )
        self.footer_label.setObjectName("Muted")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.footer_label)

        self.setCentralWidget(central)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(16)

        logo = QFrame()
        logo.setObjectName("HeaderLogo")
        logo.setFixedSize(58, 58)
        logo_layout = QVBoxLayout(logo)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_text = QLabel("F2F")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_text.setStyleSheet(
            f"color: {PALETTE['accent']}; font-size: 17px; font-weight: 900;"
        )
        logo_layout.addWidget(logo_text)
        header.addWidget(logo)

        copy = QVBoxLayout()
        copy.setSpacing(2)
        title = QLabel("Frame2File")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Ubah gambar berurutan menjadi PDF profesional")
        subtitle.setObjectName("Subtitle")
        copy.addWidget(title)
        copy.addWidget(subtitle)
        header.addLayout(copy, 1)

        return header

    def _build_folder_panel(self) -> QFrame:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Folder gambar")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setPlaceholderText("Belum ada folder dipilih")
        self.choose_folder_button = QPushButton("Pilih Folder")
        self.choose_folder_button.setObjectName("PrimaryButton")
        self.choose_folder_button.setMinimumWidth(142)
        row.addWidget(self.folder_input, 1)
        row.addWidget(self.choose_folder_button)
        layout.addLayout(row)

        return panel

    def _build_preview_panel(self) -> QFrame:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title_group = QVBoxLayout()
        title_group.setSpacing(2)
        title = QLabel("Preview thumbnail")
        title.setObjectName("SectionTitle")
        hint = QLabel("Drag thumbnail untuk mengubah urutan.")
        hint.setObjectName("Muted")
        title_group.addWidget(title)
        title_group.addWidget(hint)
        header.addLayout(title_group, 1)

        self.add_button = QPushButton("Tambah")
        self.up_button = QPushButton("Naik")
        self.down_button = QPushButton("Turun")
        self.delete_button = QPushButton("Hapus")
        self.delete_button.setObjectName("DangerButton")
        for button in (self.add_button, self.up_button, self.down_button, self.delete_button):
            button.setMinimumWidth(86)
            header.addWidget(button)

        layout.addLayout(header)

        self.thumbnail_list = ThumbnailListWidget()
        self.thumbnail_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.thumbnail_list, 1)

        return panel

    def _build_progress_panel(self) -> QFrame:
        panel = self._panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        top = QHBoxLayout()
        title = QLabel("Progress")
        title.setObjectName("SectionTitle")
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("Muted")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(title)
        top.addWidget(self.percent_label)
        layout.addLayout(top)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setObjectName("Muted")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        return panel

    def _panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        return panel

    def _connect_signals(self) -> None:
        self.choose_folder_button.clicked.connect(self.choose_folder)
        self.add_button.clicked.connect(self.add_images)
        self.up_button.clicked.connect(lambda: self.move_selected(-1))
        self.down_button.clicked.connect(lambda: self.move_selected(1))
        self.delete_button.clicked.connect(self.delete_selected)
        self.export_button.clicked.connect(self.start_export)
        self.thumbnail_list.order_changed.connect(self.on_order_changed)
        self.thumbnail_list.currentRowChanged.connect(self.update_action_states)
        self.update_action_states()

    def choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Pilih folder gambar")
        if not selected:
            return

        self.folder_path = Path(selected)
        self.folder_input.setText(str(self.folder_path))
        self._set_progress(0)
        self._set_status("Memindai folder dan membuat daftar gambar...")
        self._set_busy(True, export_busy=False)
        self._start_scan_worker(self.folder_path)

    def add_images(self) -> None:
        selected, _ = QFileDialog.getOpenFileNames(
            self,
            "Tambah gambar",
            "",
            "Gambar (*.jpg *.jpeg *.png *.webp *.bmp);;JPG (*.jpg *.jpeg);;PNG (*.png);;WEBP (*.webp);;BMP (*.bmp)",
        )
        if not selected:
            return

        added = filter_supported([Path(path) for path in selected])
        if not added:
            self._show_warning("Tidak ada gambar", "File yang dipilih tidak termasuk format yang didukung.")
            return

        if self.folder_path is None:
            self.folder_path = added[0].parent
            self.folder_input.setText(str(self.folder_path))

        first_new_row = self.thumbnail_list.count()
        for image_path in added:
            self.thumbnail_list.add_image(image_path)
        self.thumbnail_list.refresh_numbers()
        self.thumbnail_list.setCurrentRow(first_new_row)
        self._set_progress(0)
        self._set_status(f"Total {self.thumbnail_list.count()} gambar siap diproses.")
        self._start_thumbnail_worker(self.thumbnail_list.image_paths())

    def move_selected(self, direction: int) -> None:
        current = self.thumbnail_list.currentRow()
        target = current + direction
        if current < 0 or target < 0 or target >= self.thumbnail_list.count():
            return

        item = self.thumbnail_list.takeItem(current)
        self.thumbnail_list.insertItem(target, item)
        self.thumbnail_list.setCurrentRow(target)
        self.thumbnail_list.refresh_numbers()
        self._set_progress(0)
        self._set_status("Urutan gambar diperbarui.")

    def delete_selected(self) -> None:
        current = self.thumbnail_list.currentRow()
        if current < 0:
            return

        item = self.thumbnail_list.takeItem(current)
        name = item.data(Qt.ItemDataRole.UserRole + 1)
        self.thumbnail_list.refresh_numbers()
        if self.thumbnail_list.count():
            self.thumbnail_list.setCurrentRow(min(current, self.thumbnail_list.count() - 1))
        self._set_progress(0)
        self._set_status(f"Dihapus: {name}")
        self.update_action_states()

    def on_order_changed(self, _images: list) -> None:
        self._set_progress(0)
        self._set_status("Urutan gambar diperbarui.")

    def start_export(self) -> None:
        images = self.thumbnail_list.image_paths()
        if self.folder_path is None:
            self._show_warning("Belum ada folder", "Silakan pilih folder gambar terlebih dahulu.")
            return

        if not images:
            formats = ", ".join(sorted(ext.upper().lstrip(".") for ext in SUPPORTED_EXTENSIONS))
            self._show_warning("Tidak ada gambar", f"Folder ini tidak berisi {formats}.")
            return

        output_file = self.folder_path / f"{self.folder_path.name}.pdf"
        self._set_progress(0)
        self._set_status(f"Membuat PDF dari {len(images)} gambar...")
        self._set_busy(True, export_busy=True)
        self._start_export_worker(images, output_file)

    def update_action_states(self) -> None:
        count = self.thumbnail_list.count()
        row = self.thumbnail_list.currentRow()
        has_selection = row >= 0
        self.add_button.setEnabled(True)
        self.up_button.setEnabled(has_selection and row > 0)
        self.down_button.setEnabled(has_selection and row < count - 1)
        self.delete_button.setEnabled(has_selection)
        self.export_button.setEnabled(count > 0 and self._export_thread is None)

    def _start_scan_worker(self, folder: Path) -> None:
        self._scan_thread = QThread(self)
        self._scan_worker = FolderScanWorker(folder)
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.failed.connect(self._on_worker_failed)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_worker.failed.connect(self._scan_thread.quit)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)
        self._scan_thread.finished.connect(lambda: setattr(self, "_scan_thread", None))
        self._scan_thread.start()

    def _on_scan_finished(self, images: list[Path]) -> None:
        self.thumbnail_list.set_images(images)
        self._set_busy(False, export_busy=False)
        self.update_action_states()

        if images:
            self._set_status(f"Ditemukan {len(images)} gambar siap diproses.")
            self._start_thumbnail_worker(images)
        else:
            self._set_status("Tidak ada gambar yang didukung di folder ini.")

    def _start_thumbnail_worker(self, images: list[Path]) -> None:
        self._cancel_thumbnail_worker()
        if not images:
            return

        self._thumbnail_thread = QThread(self)
        self._thumbnail_worker = ThumbnailWorker(images, PALETTE["bg"])
        self._thumbnail_worker.moveToThread(self._thumbnail_thread)
        self._thumbnail_thread.started.connect(self._thumbnail_worker.run)
        self._thumbnail_worker.thumbnail_ready.connect(self._on_thumbnail_ready)
        self._thumbnail_worker.failed.connect(lambda row, _path, _error: self.thumbnail_list.mark_thumbnail_failed(row))
        self._thumbnail_worker.finished.connect(self._thumbnail_thread.quit)
        self._thumbnail_thread.finished.connect(self._thumbnail_thread.deleteLater)
        self._thumbnail_thread.finished.connect(lambda: setattr(self, "_thumbnail_thread", None))
        self._thumbnail_thread.start()

    def _cancel_thumbnail_worker(self) -> None:
        if self._thumbnail_worker is not None:
            self._thumbnail_worker.cancel()
        self._thumbnail_worker = None

    def _on_thumbnail_ready(self, _index: int, path: str, data: bytes, width: int, height: int) -> None:
        self.thumbnail_list.set_thumbnail(Path(path), data, width, height)

    def _start_export_worker(self, images: list[Path], output_file: Path) -> None:
        self._export_thread = QThread(self)
        self._export_worker = PdfExportWorker(images, output_file)
        self._export_worker.moveToThread(self._export_thread)
        self._export_thread.started.connect(self._export_worker.run)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished.connect(self._on_export_finished)
        self._export_worker.failed.connect(self._on_export_failed)
        self._export_worker.finished.connect(self._export_thread.quit)
        self._export_worker.failed.connect(self._export_thread.quit)
        self._export_thread.finished.connect(self._export_thread.deleteLater)
        self._export_thread.finished.connect(lambda: setattr(self, "_export_thread", None))
        self._export_thread.finished.connect(self.update_action_states)
        self._export_thread.start()

    def _on_export_progress(self, progress: int, current: int, total: int) -> None:
        self._set_progress(progress)
        self._set_status(f"Memproses gambar {current} dari {total}...")

    def _on_export_finished(self, output_file: str, total: int) -> None:
        self._set_progress(100)
        self._set_status(f"Selesai! {total} gambar disimpan ke {output_file}")
        self._set_busy(False, export_busy=True)

    def _on_export_failed(self, error: str) -> None:
        self._set_status("Gagal membuat PDF.")
        self._set_busy(False, export_busy=True)
        self._show_error("Terjadi kesalahan", error)

    def _on_worker_failed(self, error: str) -> None:
        self._set_busy(False, export_busy=False)
        self._set_status("Gagal memproses folder.")
        self._show_error("Terjadi kesalahan", error)

    def _set_progress(self, value: int) -> None:
        value = max(0, min(value, 100))
        self.progress_bar.setValue(value)
        self.percent_label.setText(f"{value}%")

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _set_busy(self, busy: bool, export_busy: bool) -> None:
        self.choose_folder_button.setEnabled(not busy)
        self.add_button.setEnabled(not busy)
        self.up_button.setEnabled(not busy)
        self.down_button.setEnabled(not busy)
        self.delete_button.setEnabled(not busy)
        self.thumbnail_list.setEnabled(not busy or export_busy)
        self.export_button.setEnabled(not busy and self.thumbnail_list.count() > 0)
        if export_busy:
            self.export_button.setText("Membuat PDF..." if busy else "Buat PDF")

    def _show_warning(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _enable_dark_title_bar(self) -> None:
        if sys.platform != "win32":
            return

        try:
            hwnd = int(self.winId())
            enabled = ctypes.c_int(1)
            for attribute in (20, 19):
                result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    attribute,
                    ctypes.byref(enabled),
                    ctypes.sizeof(enabled),
                )
                if result == 0:
                    break
        except Exception:
            pass


def run() -> int:
    app = QApplication(sys.argv)
    from frame2file.gui.resources.theme import app_stylesheet

    app.setStyle("Fusion")
    app.setStyleSheet(app_stylesheet())
    window = MainWindow()
    window.show()
    return app.exec()

