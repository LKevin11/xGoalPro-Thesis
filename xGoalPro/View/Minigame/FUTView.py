from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QStackedLayout,
    QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QPalette, QColor
import os
from ResourcePath import resource_path


class FUTMainView(QWidget):
    """
    The main container widget for the FUT (Pack Opener) mini-game.

    Manages switching between the pack-opening interface and the user's card
    collection using a QStackedLayout. Coordinates signals for navigation,
    pack opening, and collection interactions.

    Signals:
        return_to_hub (): Emitted when the user navigates back to the main hub.
        prev_btn_clicked (int): Emitted when navigating to the previous page in collection.
        next_btn_clicked (int): Emitted when navigating to the next page in collection.
        open_btn_clicked (): Emitted when the user clicks the "Open Pack" button.
        collection_btn_clicked (int): Emitted when opening the collection, passing the starting index.
    """

    return_to_hub: pyqtSignal = pyqtSignal()
    prev_btn_clicked: pyqtSignal(int) = pyqtSignal(int)
    next_btn_clicked: pyqtSignal(int) = pyqtSignal(int)
    open_btn_clicked: pyqtSignal = pyqtSignal()
    collection_btn_clicked: pyqtSignal(int) = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("FUTPage")
        self.setWindowTitle("xGoalPro - Pack Opener")

        # Dark theme background
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0d1b2a"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Stacked layout (Index + Collection)
        self.stacked_layout = QStackedLayout()
        self.index_view = FUTIndexView()
        self.collection_view = FUTCollectionView()

        self.stacked_layout.addWidget(self.index_view)
        self.stacked_layout.addWidget(self.collection_view)
        self.setLayout(self.stacked_layout)

        # Connect signals
        self.index_view.collection_btn_clicked.connect(self.show_collection)
        self.collection_view.return_to_index.connect(self.show_index)
        self.index_view.open_btn_clicked.connect(lambda: self.open_btn_clicked.emit())
        self.index_view.return_to_hub.connect(lambda: self.return_to_hub.emit())
        self.collection_view.prev_btn_clicked.connect(lambda: self.prev_btn_clicked.emit(-1))
        self.collection_view.next_btn_clicked.connect(lambda: self.next_btn_clicked.emit(1))

        # Load QSS
        self.__load_stylesheet()

    def show_index(self):
        self.stacked_layout.setCurrentWidget(self.index_view)

    def show_collection(self):
        self.stacked_layout.setCurrentWidget(self.collection_view)
        self.collection_view.disable_prev_btn()
        self.collection_view.disable_next_btn()
        self.collection_btn_clicked.emit(0)

    def refresh_collection_view(self, images):
        self.collection_view.refresh_view(images)

    def set_pack_image(self, path):
        self.index_view.set_pixmap(path)

    def set_pack_image_from_bytes(self, content):
        self.index_view.set_pixmap_from_bytes(content)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/fut_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())


class FUTIndexView(QWidget):
    """
    The index view for the FUT mini-game.

    Displays the main pack-opening interface, including pack image, open button,
    and a button to access the user's collection. Provides navigation back to hub.

    Signals:
        return_to_hub (): Emitted when the user clicks the back button.
        open_btn_clicked (): Emitted when the "Open Pack" button is clicked.
        collection_btn_clicked (): Emitted when the "My Collection" button is clicked.
    """

    return_to_hub: pyqtSignal = pyqtSignal()
    open_btn_clicked: pyqtSignal = pyqtSignal()
    collection_btn_clicked: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("FUTIndexView")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 60)
        layout.setSpacing(40)

        # Top bar (back button)
        top_bar = QHBoxLayout()
        self.return_btn = QPushButton("Back to Hub")
        self.return_btn.setObjectName("homeButton")
        self.return_btn.clicked.connect(lambda: self.return_to_hub.emit())
        top_bar.addWidget(self.return_btn, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Center content
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(25)

        title = QLabel("Pack Opener")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        subtitle = QLabel("This game is currently unavailable with the free plan!")
        subtitle.setObjectName("subTitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: red;")
        content_layout.addWidget(subtitle)

        self.image = QLabel()
        pixmap = QPixmap(resource_path("./Assets/pack_image.png"))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image.setPixmap(pixmap)
        self.image.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.image)

        self.open_btn = QPushButton("Open Pack")
        self.open_btn.setObjectName("primaryButton")
        self.open_btn.clicked.connect(lambda: self.open_btn_clicked.emit())
        content_layout.addWidget(self.open_btn, alignment=Qt.AlignCenter)

        self.collection_btn = QPushButton("My Collection")
        self.collection_btn.setObjectName("secondaryButton")
        self.collection_btn.clicked.connect(lambda: self.collection_btn_clicked.emit())
        content_layout.addWidget(self.collection_btn, alignment=Qt.AlignCenter)

        layout.addLayout(content_layout)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def set_pixmap(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.image.setPixmap(pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def set_pixmap_from_bytes(self, content):
        pixmap = QPixmap()
        pixmap.loadFromData(content)
        if not pixmap.isNull():
            self.image.setPixmap(pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))


class FUTCollectionView(QWidget):
    """
    The collection view for the FUT mini-game.

    Displays a paginated grid of collected cards, with navigation buttons to
    move through pages and return to the pack-opening interface.

    Signals:
        return_to_index (): Emitted when returning to the index view.
        prev_btn_clicked (): Emitted when the previous page button is clicked.
        next_btn_clicked (): Emitted when the next page button is clicked.

    Attributes:
        rows (list[QHBoxLayout]): Layouts representing rows of card images.
        prev_btn (QPushButton): Button to navigate to the previous page.
        next_btn (QPushButton): Button to navigate to the next page.
    """

    return_to_index: pyqtSignal = pyqtSignal()
    prev_btn_clicked: pyqtSignal = pyqtSignal()
    next_btn_clicked: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("FUTCollectionView")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(25)

        # Top bar
        top_bar = QHBoxLayout()
        self.return_btn = QPushButton("← Open Packs")
        self.return_btn.setObjectName("homeButton")
        self.return_btn.clicked.connect(lambda: self.return_to_index.emit())
        top_bar.addWidget(self.return_btn, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Title
        title = QLabel("My Card Collection")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Image grid (2 rows × 3 cols)
        self.rows = [QHBoxLayout(), QHBoxLayout()]
        for row in self.rows:
            row.setSpacing(25)
            row.setAlignment(Qt.AlignCenter)
            for _ in range(3):
                label = QLabel()
                label.setFixedSize(140, 140)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("background-color: #1b263b; border-radius: 12px;")
                row.addWidget(label)
            layout.addLayout(row)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setAlignment(Qt.AlignCenter)
        nav_layout.setSpacing(20)

        self.prev_btn = QPushButton("← Prev")
        self.prev_btn.setObjectName("secondaryButton")
        self.prev_btn.clicked.connect(lambda: self.prev_btn_clicked.emit())
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next →")
        self.next_btn.setObjectName("secondaryButton")
        self.next_btn.clicked.connect(lambda: self.next_btn_clicked.emit())
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def refresh_view(self, images):
        labels = []
        for row in self.rows:
            for i in range(row.count()):
                labels.append(row.itemAt(i).widget())

        for idx, label in enumerate(labels):
            if idx < len(images):
                pixmap = QPixmap()
                pixmap.loadFromData(images[idx])
                label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                label.clear()

    def disable_prev_btn(self):
        self.prev_btn.setEnabled(False)

    def enable_prev_btn(self):
        self.prev_btn.setEnabled(True)

    def disable_next_btn(self):
        self.next_btn.setEnabled(False)

    def enable_next_btn(self):
        self.next_btn.setEnabled(True)
