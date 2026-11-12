
import sys
import os
import glob
import numpy as np
import pydicom

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSlider, QFileDialog,
    QComboBox, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg


class DicomCanvas(FigureCanvasQTAgg):
    """DICOM画像を表示するMatplotlib Canvas"""

    def __init__(self, orientation, parent=None):
        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)

        super().__init__(self.figure)
        self.orientation = orientation
        self.parent_viewer = parent

        self.figure.patch.set_facecolor("black")
        self.ax.set_facecolor("black")
        self.ax.axis("off")

        self.mpl_connect("button_press_event", self.on_click)

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        if self.parent_viewer is not None:
            self.parent_viewer.update_crosshair(
                self.orientation,
                event.xdata,
                event.ydata
            )


class DicomViewer(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Python DICOM MPR Viewer")
        self.resize(1400, 900)

        # Volume data
        self.volume = None

        # Current voxel position
        self.x = 0
        self.y = 0
        self.z = 0

        # Window Width / Level
        self.ww = 400
        self.wl = 40

        # Main orientation
        self.main_orientation = "Axial"

        self.canvases = {}

        self.init_ui()

    # -----------------------------------
    # UI
    # -----------------------------------

    def init_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Menu
        self.create_menu()

        # Orientation selection
        control_layout = QHBoxLayout()

        control_layout.addWidget(QLabel("Main View:"))

        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems([
            "Axial",
            "Coronal",
            "Sagittal"
        ])

        self.orientation_combo.currentTextChanged.connect(
            self.change_orientation
        )

        control_layout.addWidget(self.orientation_combo)
        control_layout.addStretch()

        main_layout.addLayout(control_layout)

        # Image views
        image_layout = QGridLayout()

        self.canvases = {
            "Axial": DicomCanvas("Axial", self),
            "Coronal": DicomCanvas("Coronal", self),
            "Sagittal": DicomCanvas("Sagittal", self)
        }

        self.view_labels = {}

        for name in self.canvases:
            self.view_labels[name] = QLabel(name)
            self.view_labels[name].setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.view_labels[name].setStyleSheet(
                "color: white; font-weight: bold;"
                "background-color: #333333;"
            )

        self.image_layout = image_layout
        main_layout.addLayout(image_layout, stretch=1)

        self.update_view_layout()

        # --------------------------------
        # Slice controls
        # --------------------------------

        slice_group = QGroupBox("Slice Position")
        slice_layout = QHBoxLayout(slice_group)

        self.slice_label = QLabel("Slice: 0")

        self.slice_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        self.slice_slider.valueChanged.connect(
            self.change_slice
        )

        slice_layout.addWidget(self.slice_label)
        slice_layout.addWidget(self.slice_slider)

        main_layout.addWidget(slice_group)

        # --------------------------------
        # WW / WL controls
        # --------------------------------

        ww_group = QGroupBox("Window / Level")
        ww_layout = QGridLayout(ww_group)

        self.ww_label = QLabel("WW: 400")
        self.wl_label = QLabel("WL: 40")

        self.ww_slider = QSlider(
            Qt.Orientation.Horizontal
        )
        self.ww_slider.setRange(1, 4000)
        self.ww_slider.setValue(self.ww)

        self.wl_slider = QSlider(
            Qt.Orientation.Horizontal
        )
        self.wl_slider.setRange(-1000, 3000)
        self.wl_slider.setValue(self.wl)

        self.ww_slider.valueChanged.connect(
            self.change_ww
        )

        self.wl_slider.valueChanged.connect(
            self.change_wl
        )

        ww_layout.addWidget(self.ww_label, 0, 0)
        ww_layout.addWidget(self.ww_slider, 0, 1)

        ww_layout.addWidget(self.wl_label, 1, 0)
        ww_layout.addWidget(self.wl_slider, 1, 1)

        main_layout.addWidget(ww_group)

        self.statusBar().showMessage(
            "DICOMファイルを読み込んでください"
        )

    # -----------------------------------
    # Menu
    # -----------------------------------

    def create_menu(self):

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        open_file = file_menu.addAction("Open DICOM Files")
        open_file.triggered.connect(
            self.open_dicom_files
        )

        open_folder = file_menu.addAction("Open DICOM Folder")
        open_folder.triggered.connect(
            self.open_dicom_folder
        )

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

    # -----------------------------------
    # DICOM loading
    # -----------------------------------

    def open_dicom_files(self):

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select DICOM Files",
            "",
            "All Files (*)"
        )

        if files:
            self.load_dicom(files)

    def open_dicom_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select DICOM Folder"
        )

        if folder:
            files = glob.glob(
                os.path.join(folder, "**", "*"),
                recursive=True
            )

            files = [
                f for f in files if os.path.isfile(f)
            ]

            self.load_dicom(files)

    def load_dicom(self, files):

        datasets = []

        for filename in files:

            try:
                ds = pydicom.dcmread(
                    filename,
                    force=False
                )

                if not hasattr(ds, "PixelData"):
                    continue

                if getattr(ds, "SamplesPerPixel", 1) != 1:
                    continue

                datasets.append(ds)

            except Exception:
                continue

        if not datasets:
            QMessageBox.warning(
                self,
                "Error",
                "有効なDICOM画像がありません"
            )
            return

        try:
            # Sort slices by patient Z position
            datasets.sort(
                key=lambda ds: (
                    float(ds.ImagePositionPatient[2])
                    if hasattr(ds, "ImagePositionPatient")
                    else float(getattr(ds, "InstanceNumber", 0))
                )
            )

            # Convert to HU / modality values
            images = []

            for ds in datasets:

                image = ds.pixel_array.astype(np.float32)

                slope = float(
                    getattr(ds, "RescaleSlope", 1)
                )

                intercept = float(
                    getattr(ds, "RescaleIntercept", 0)
                )

                image = image * slope + intercept

                images.append(image)

            shape = images[0].shape

            if any(img.shape != shape for img in images):
                raise ValueError(
                    "スライス間で画像サイズが一致しません"
                )

            # 3D volume: Z, Y, X
            self.volume = np.stack(images, axis=0)

            self.z = len(images) // 2
            self.y = shape[0] // 2
            self.x = shape[1] // 2

            # Initial WW / WL
            minimum = float(np.percentile(self.volume, 1))
            maximum = float(np.percentile(self.volume, 99))

            self.ww = max(1, int(maximum - minimum))
            self.wl = int((maximum + minimum) / 2)

            self.ww_slider.setValue(
                min(4000, self.ww)
            )
            self.wl_slider.setValue(
                min(3000, max(-1000, self.wl))
            )

            self.update_slice_slider()
            self.update_all_views()

            self.statusBar().showMessage(
                f"Loaded: {len(images)} slices "
                f"| Volume: {self.volume.shape}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "DICOM Loading Error",
                str(e)
            )

    # -----------------------------------
    # Main view switching
    # -----------------------------------

    def change_orientation(self, orientation):

        self.main_orientation = orientation

        self.update_view_layout()
        self.update_slice_slider()
        self.update_all_views()

    def update_view_layout(self):

        # Remove existing widgets
        while self.image_layout.count():
            item = self.image_layout.takeAt(0)

            if item.widget():
                item.widget().setParent(None)

        main = self.main_orientation

        others = [
            name for name in self.canvases
            if name != main
        ]

        # Main view on left
        self.image_layout.addWidget(
            self.view_labels[main], 0, 0
        )

        self.image_layout.addWidget(
            self.canvases[main], 1, 0, 2, 1
        )

        # Sub views on right
        for i, name in enumerate(others):

            self.image_layout.addWidget(
                self.view_labels[name], i * 2, 1
            )

            self.image_layout.addWidget(
                self.canvases[name], i * 2 + 1, 1
            )

        self.image_layout.setColumnStretch(0, 2)
        self.image_layout.setColumnStretch(1, 1)

        self.image_layout.setRowStretch(1, 2)
        self.image_layout.setRowStretch(3, 1)

    # -----------------------------------
    # Slice slider
    # -----------------------------------

    def update_slice_slider(self):

        if self.volume is None:
            return

        axis = {
            "Axial": 0,
            "Coronal": 1,
            "Sagittal": 2
        }[self.main_orientation]

        maximum = self.volume.shape[axis] - 1

        self.slice_slider.blockSignals(True)

        self.slice_slider.setRange(0, maximum)

        position = {
            "Axial": self.z,
            "Coronal": self.y,
            "Sagittal": self.x
        }[self.main_orientation]

        self.slice_slider.setValue(position)

        self.slice_slider.blockSignals(False)

        self.slice_label.setText(
            f"Slice: {position + 1} / {maximum + 1}"
        )

    def change_slice(self, value):

        if self.volume is None:
            return

        if self.main_orientation == "Axial":
            self.z = value

        elif self.main_orientation == "Coronal":
            self.y = value

        elif self.main_orientation == "Sagittal":
            self.x = value

        self.update_slice_slider()
        self.update_all_views()

    # -----------------------------------
    # Crosshair synchronization
    # -----------------------------------

    def update_crosshair(self, orientation, px, py):

        if self.volume is None:
            return

        if orientation == "Axial":

            self.x = int(np.clip(
                round(px), 0, self.volume.shape[2] - 1
            ))

            self.y = int(np.clip(
                round(py), 0, self.volume.shape[1] - 1
            ))

        elif orientation == "Coronal":

            self.x = int(np.clip(
                round(px), 0, self.volume.shape[2] - 1
            ))

            self.z = int(np.clip(
                round(py), 0, self.volume.shape[0] - 1
            ))

        elif orientation == "Sagittal":

            self.y = int(np.clip(
                round(px), 0, self.volume.shape[1] - 1
            ))

            self.z = int(np.clip(
                round(py), 0, self.volume.shape[0] - 1
            ))

        self.update_slice_slider()
        self.update_all_views()

    # -----------------------------------
    # WW / WL
    # -----------------------------------

    def change_ww(self, value):

        self.ww = value
        self.ww_label.setText(f"WW: {value}")

        self.update_all_views()

    def change_wl(self, value):

        self.wl = value
        self.wl_label.setText(f"WL: {value}")

        self.update_all_views()

    # -----------------------------------
    # Display images
    # -----------------------------------

    def update_all_views(self):

        if self.volume is None:
            return

        self.display_image("Axial")
        self.display_image("Coronal")
        self.display_image("Sagittal")

    def display_image(self, orientation):

        canvas = self.canvases[orientation]
        ax = canvas.ax

        ax.clear()
        ax.set_facecolor("black")
        ax.axis("off")

        if orientation == "Axial":

            image = self.volume[self.z, :, :]

            cross_x = self.x
            cross_y = self.y

        elif orientation == "Coronal":

            image = self.volume[:, self.y, :]

            cross_x = self.x
            cross_y = self.z

        else:

            image = self.volume[:, :, self.x]

            cross_x = self.y
            cross_y = self.z

        vmin = self.wl - self.ww / 2
        vmax = self.wl + self.ww / 2

        ax.imshow(
            image,
            cmap="gray",
            origin="lower",
            vmin=vmin,
            vmax=vmax,
            interpolation="nearest"
        )

        # Crosshair
        ax.axvline(
            cross_x,
            color="red",
            linewidth=0.8
        )

        ax.axhline(
            cross_y,
            color="red",
            linewidth=0.8
        )

        ax.set_title(
            orientation,
            color="white"
        )

        canvas.draw_idle()


# -----------------------------------
# Main
# -----------------------------------

if __name__ == "__main__":

    app = QApplication(sys.argv)

    viewer = DicomViewer()
    viewer.show()

    sys.exit(app.exec())
