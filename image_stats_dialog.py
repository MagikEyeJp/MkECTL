from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QLabel, QWidget, QStackedLayout
)
import pyqtgraph as pg
import numpy as np
from PySide6.QtGui import QImage
import ImageViewScene

class ImageStatsDialog(QDialog):
    def __init__(self, viewer: ImageViewScene = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Statistics")
        self.resize(500, 400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.viewer = viewer

        # Mode selection
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Histogram", "Pixel Info"])
        self.mode_selector.currentIndexChanged.connect(self.change_mode)
        layout.addWidget(self.mode_selector)

        # Central stack
        self.stack_layout = QStackedLayout()
        layout.addLayout(self.stack_layout)

        # Mode 0: Histogram + stats
        self.histogram_plot = pg.PlotWidget(title="Histogram")
        self.histogram_stats = QLabel("Stats will appear here.")
        hist_widget = QWidget()
        hist_layout = QVBoxLayout()
        hist_layout.addWidget(self.histogram_plot)
        hist_layout.addWidget(self.histogram_stats)
        hist_widget.setLayout(hist_layout)
        self.stack_layout.addWidget(hist_widget)

        # Mode 1: Pixel info (stub)
        self.pixel_info = QLabel("Pixel zoom and value will appear here.")
        pixel_widget = QWidget()
        pixel_layout = QVBoxLayout()
        pixel_layout.addWidget(self.pixel_info)
        pixel_widget.setLayout(pixel_layout)
        self.stack_layout.addWidget(pixel_widget)

        qimage = viewer.getQImage()
        self.update_image(qimage)

    def change_mode(self, index):
        self.stack_layout.setCurrentIndex(index)
        if index == 0:  # Histogram
            self.viewer.set_mode("none")
        elif index == 1: # Pixel Info
            self.viewer.set_mode("pixel")
            self.viewer.on_pixel_selected = self.update_pixel_info

    def update_image(self, qimage: QImage):
        self.histogram_plot.clear()

        if not qimage or qimage.isNull():
            self.histogram_stats.setText("No image loaded.")
            self.pixel_info.setText("No image loaded.")
            return

        arr = self.qimage_to_array(qimage)
        self.current_array = arr 
        self.show_histogram(arr)
        self.show_stats(arr)

    def qimage_to_array(self, qimage: QImage) -> np.ndarray:
        qimage = qimage.convertToFormat(QImage.Format.Format_Grayscale8)
        width = qimage.width()
        height = qimage.height()
        bytes_per_line = qimage.bytesPerLine()
        ptr = qimage.bits()
        buf = ptr.tobytes()
        arr = np.frombuffer(buf, np.uint8).reshape((height, bytes_per_line))
        return arr[:, :width].copy()

    def show_histogram(self, arr: np.ndarray):
        bins = np.arange(257)
        y, x = np.histogram(arr, bins=bins)
        print(y[0])
        self.histogram_plot.plot(
            x, y,
            stepMode=True,
            fillLevel=0,
            brush=(150, 150, 255, 150),
            clear=True
        )
        self.histogram_plot.setLabel("bottom", "Pixel Intensity")
        self.histogram_plot.setLabel("left", "Count")

    def show_stats(self, arr: np.ndarray):
        mean = np.mean(arr)
        std = np.std(arr)
        min_val = np.min(arr)
        max_val = np.max(arr)
        roi = self.viewer.get_roi_rect()
        if roi is not None:
            x0, y0, x1, y1 = roi
        else:
            x0, y0, x1, y1 = -1, -1, -1, -1
        self.histogram_stats.setText(
            f"Mean: {mean:.2f}, StdDev: {std:.2f}\n"
            f"Min: {min_val}, Max: {max_val}\n"
            f"roi: {x0}, {y0}, {x1}, {y1}\n"
        )

    def update_pixel_info(self, x: int, y: int):
        if self.current_array is None:
            self.pixel_info.setText("No image available.")
            return

        arr = self.current_array
        h, w = arr.shape

        # Define zoom window (8x8)
        size = 8
        half = size // 2
        x0 = max(0, x - half)
        y0 = max(0, y - half)
        x1 = min(w, x + half)
        y1 = min(h, y + half)

        sub_img = arr[y0:y1, x0:x1]

        center_val = arr[y, x] if 0 <= x < w and 0 <= y < h else "N/A"

        text = f"Pixel ({x}, {y}) = {center_val}\n\n"
        text += "Zoomed Area:\n"
        for row in sub_img:
            text += " ".join(f"{v:3d}" for v in row) + "\n"

        self.pixel_info.setText(text)

