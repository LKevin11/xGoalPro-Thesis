from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QLabel,
    QFormLayout, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
from ResourcePath import resource_path


class LoginPage(QWidget):
    """
    A custom QWidget that represents the login screen of the xGoalPro application.

    This page provides a user interface for logging in, including username and
    password fields, a login button, and navigation options for returning home or
    switching to the registration page. It emits signals for key user interactions
    such as login attempts and navigation actions.

    Signals:
        login_btn_clicked (str, str): Emitted when the login button is pressed,
            passing the entered username and password.
        switch_to_reg_btn_clicked (): Emitted when the user clicks the "Sign up"
            button to switch to the registration page.
        return_to_home (): Emitted when the user clicks the "Home" button.

    Attributes:
        register_btn (QPushButton): Button to switch to the registration page.
        name_edit (QLineEdit): Input field for the username.
        pass_edit (QLineEdit): Input field for the password.
    """
    # === Signals ===
    login_btn_clicked = pyqtSignal(str, str)
    switch_to_reg_btn_clicked = pyqtSignal()
    return_to_home = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("LoginPage")
        self.setWindowTitle("xGoalPro - Login")

        self.register_btn = QPushButton()
        self.name_edit = QLineEdit()
        self.pass_edit = QLineEdit()

        self.__init_ui()
        self.__load_stylesheet()

    # === Events ===
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.attempt_login()

    # === Methods ===
    def attempt_login(self) -> None:
        username = self.name_edit.text().strip()
        password = self.pass_edit.text().strip()
        self.login_btn_clicked.emit(username, password)

    def clear_form(self) -> None:
        self.name_edit.clear()
        self.pass_edit.clear()

    def __init_ui(self) -> None:
        # === Root layout ===
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(80, 50, 80, 50)
        root_layout.setSpacing(20)

        # === Top bar (home button only) ===
        top_bar = QHBoxLayout()
        top_bar.setAlignment(Qt.AlignLeft)

        home_btn = QPushButton("🏠 Home")
        home_btn.setObjectName("homeButton")
        home_btn.clicked.connect(lambda: self.return_to_home.emit())
        top_bar.addWidget(home_btn)

        root_layout.addLayout(top_bar)

        # === Main content (centered) ===
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(25)

        # === Logo ===
        logo_label = QLabel()
        logo_path = resource_path("./Assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("xGoalPro")
        logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo_label)

        # === Titles ===
        title = QLabel("Welcome Back!")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sub_title = QLabel("Login to your account")
        sub_title.setObjectName("subTitleLabel")
        sub_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(sub_title)

        # === Form Layout ===
        form_layout = QFormLayout()
        form_layout.setFormAlignment(Qt.AlignCenter)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(15)

        self.name_edit.setPlaceholderText("Enter your username")
        self.name_edit.setObjectName("inputField")
        form_layout.addRow(self.name_edit)

        self.pass_edit.setPlaceholderText("Enter your password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setObjectName("inputField")
        form_layout.addRow(self.pass_edit)

        main_layout.addLayout(form_layout)

        # === Login button ===
        login_btn = QPushButton("Login")
        login_btn.setObjectName("loginButton")
        login_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        login_btn.clicked.connect(self.attempt_login)
        main_layout.addWidget(login_btn, alignment=Qt.AlignCenter)

        # === Register section ===
        register_layout = QHBoxLayout()
        register_layout.setAlignment(Qt.AlignCenter)

        register_label = QLabel("Don't have an account?")
        register_label.setObjectName("registerLabel")
        self.register_btn = QPushButton("Sign up")
        self.register_btn.setObjectName("registerButton")
        self.register_btn.clicked.connect(lambda: self.switch_to_reg_btn_clicked.emit())

        register_layout.addWidget(register_label)
        register_layout.addWidget(self.register_btn)
        main_layout.addLayout(register_layout)

        # Add all content to root layout
        root_layout.addLayout(main_layout)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/login_page.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
