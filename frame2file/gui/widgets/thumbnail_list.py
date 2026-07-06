from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QBrush, QColor, QDragEnterEvent, QDropEvent, QImage, QPixmap
from PySide6.QtWidgets import QListWidget, QListWidgetItem


PATH_ROLE = Qt.ItemDataRole.UserRole
NAME_ROLE = Qt.ItemDataRole.UserRole + 1


class ThumbnailListWidget(QListWidget):
    order_changed = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ThumbnailList")
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setMovement(QListWidget.Movement.Snap)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setWrapping(True)
        self.setUniformItemSizes(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setIconSize(QSize(198, 222))
        self.setGridSize(QSize(232, 292))
        self.setSpacing(14)
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def set_images(self, images: list[Path]) -> None:
        self.clear()
        for image_path in images:
            self.add_image(image_path)
        self.refresh_numbers()
        if self.count():
            self.setCurrentRow(0)

    def add_image(self, image_path: Path) -> None:
        item = QListWidgetItem()
        item.setData(PATH_ROLE, str(image_path))
        item.setData(NAME_ROLE, image_path.name)
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
        )
        self.addItem(item)

    def image_paths(self) -> list[Path]:
        return [Path(self.item(index).data(PATH_ROLE)) for index in range(self.count())]

    def refresh_numbers(self) -> None:
        for index in range(self.count()):
            item = self.item(index)
            item.setText(f"{index + 1}. {item.data(NAME_ROLE)}")

    def set_thumbnail(self, image_path: Path, data: bytes, width: int, height: int) -> None:
        matches = self.findItems(image_path.name, Qt.MatchFlag.MatchContains)
        target = None
        for item in matches:
            if item.data(PATH_ROLE) == str(image_path):
                target = item
                break

        if target is None:
            return

        image = QImage(data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
        target.setIcon(QPixmap.fromImage(image))

    def mark_thumbnail_failed(self, row: int) -> None:
        item = self.item(row)
        if item is None:
            return
        item.setForeground(QBrush(QColor("#e65b66")))

    def dropEvent(self, event: QDropEvent) -> None:
        super().dropEvent(event)
        self.refresh_numbers()
        self.order_changed.emit(self.image_paths())

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.acceptProposedAction()

