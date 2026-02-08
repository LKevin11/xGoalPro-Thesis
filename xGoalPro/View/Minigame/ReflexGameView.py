from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QDesktopWidget
from ResourcePath import resource_path


class GameField(QWidget):
    """
    The QWidget representing the game field for Reflex Football Goalkeeper.

    Draws balls, paddle, score, lives, instructions, and game-over messages.
    Handles mouse and keyboard input for moving the paddle and controlling the game.

    Signals:
        move_paddle_signal (float): Emitted with the x-coordinate of the paddle.
        key_press_signal (int): Emitted with the pressed key code.
        key_release_signal (int): Emitted with the released key code.
        mouse_press_signal (): Emitted when the mouse is clicked.
    """

    move_paddle_signal = pyqtSignal(float)
    key_press_signal = pyqtSignal(int)
    key_release_signal = pyqtSignal(int)
    mouse_press_signal = pyqtSignal()

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.setMinimumSize(model.width, model.height)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.model.updated.connect(self.update)

        self.ball_image: QPixmap = QPixmap(resource_path("./Assets/ball.png"))
        self.paddle_image: QPixmap = QPixmap(resource_path("./Assets/gloves.png"))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(13, 27, 42))
        for b in self.model.balls:
            size = int(b.radius * 2)
            img = self.ball_image.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawPixmap(int(b.x - b.radius), int(b.y - b.radius), img)
        pad = self.model.paddle
        w, h = int(pad.width), int(pad.height * 10)  # scale gloves image nicely
        img = self.paddle_image.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(int(pad.x - w/2), int(pad.y - h/2), img)

        p.setPen(QPen(QColor(230, 230, 230)))
        p.setFont(QFont('Arial', 14))
        p.drawText(12, 24, f"Score: {self.model.score}")
        p.drawText(12, 48, f"Lives: {self.model.lives}")
        if self.model.paused:
            p.setFont(QFont('Arial', 36))
            p.drawText(self.rect(), Qt.AlignCenter, "PAUSED")
        if self.model.show_instructions:
            self.__draw_instructions(p)
        if self.model.is_game_over:
            self.__draw_game_over(p)

    def mouseMoveEvent(self, event):
        if not self.model.show_instructions:
            self.move_paddle_signal.emit(event.x())

    def mousePressEvent(self, event):
        self.mouse_press_signal.emit()

    def keyPressEvent(self, event):
        self.key_press_signal.emit(event.key())

    def keyReleaseEvent(self, event):
        self.key_release_signal.emit(event.key())

    def __draw_instructions(self, p: QPainter) -> None:
        p.setPen(QPen(QColor(255, 255, 255)))
        p.setFont(QFont('Arial', 20))
        text = ("REFLEX GOALKEEPER\n\n"
                "Move paddle with MOUSE or ARROWS\n"
                "Keep balls in play!\n"
                "Each ball disappears after 3 saves.\n\n"
                "Controls:\n"
                "SPACE - Pause/Resume\nR - Restart\nClick to Start")
        p.drawText(self.rect(), Qt.AlignCenter, text)

    def __draw_game_over(self, p: QPainter) -> None:
        p.setPen(QPen(QColor(255, 80, 80)))
        p.setFont(QFont('Arial', 36))
        p.drawText(self.rect(), Qt.AlignCenter, f"GAME OVER\nScore: {self.model.score}\nClick or R to Restart")


class ReflexGameView(QWidget):
    """
    The main view for the Reflex Football Goalkeeper mini-game.

    Contains a title bar with a back button and the GameField widget.
    Passes input signals from the GameField to external handlers and manages layout.

    Signals:
        back_btn_pressed (): Emitted when the back button is pressed.
        move_paddle_signal (float): Forwarded from the GameField.
        key_press_signal (int): Forwarded from the GameField.
        key_release_signal (int): Forwarded from the GameField.
        mouse_press_signal (): Forwarded from the GameField.
    """


    back_btn_pressed: pyqtSignal = pyqtSignal()
    move_paddle_signal = pyqtSignal(float)
    key_press_signal = pyqtSignal(int)
    key_release_signal = pyqtSignal(int)
    mouse_press_signal = pyqtSignal()

    def __init__(self, model):
        super().__init__()

        self.setWindowTitle("xGoalPro - Reflex Game")

        self.model = model

        # Overall layout
        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Title bar ---
        title_bar: QWidget = QWidget()
        title_bar.setStyleSheet("background-color: #1e324e; padding: 8px;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 4, 12, 4)

        back_button: QPushButton = QPushButton("← Back")
        back_button.setStyleSheet("background-color: #415a77; color: white;")
        back_button.clicked.connect(lambda: self.back_btn_pressed.emit())

        title_label: QLabel = QLabel("Reflex Football Goalkeeper")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00b87b; font-size: 20px; font-weight: bold;")

        title_layout.addWidget(back_button, alignment=Qt.AlignLeft)
        title_layout.addWidget(title_label, alignment=Qt.AlignCenter)
        title_layout.addStretch()

        main_layout.addWidget(title_bar)

        # --- Game field ---
        self.game_view: GameField = GameField(model)
        self.game_view.setSizePolicy(self.game_view.sizePolicy().Expanding,
                                     self.game_view.sizePolicy().Expanding)

        main_layout.addWidget(self.game_view, stretch=1)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.game_view.move_paddle_signal.connect(lambda num: self.move_paddle_signal.emit(num))
        self.game_view.key_press_signal.connect(lambda num: self.key_press_signal.emit(num))
        self.game_view.key_release_signal.connect(lambda num: self.key_release_signal.emit(num))
        self.game_view.mouse_press_signal.connect(lambda: self.mouse_press_signal.emit())

    def showEvent(self, event):
        """Center window when shown."""
        super().showEvent(event)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
