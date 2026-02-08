from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QLabel,
    QFormLayout, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
from ResourcePath import resource_path


class RegisterPage(QWidget):
    """
    A custom QWidget representing the registration screen of the xGoalPro application.

    This page allows users to create a new account by entering their username,
    email, password, and password confirmation. It provides navigation options
    to return to the home screen or switch to the login page and emits signals
    when these actions occur.

    Signals:
        registration_btn_clicked (str, str, str, str): Emitted when the user clicks
            the "Register" button, passing username, email, password, and confirmation.
        switch_to_log_btn_clicked (): Emitted when the user opts to switch to
            the login page.
        return_to_home (): Emitted when the "Home" button is clicked.

    Attributes:
        login_btn (QPushButton): Button to navigate to the login page.
        name_edit (QLineEdit): Input field for the username.
        email_edit (QLineEdit): Input field for the email.
        pass_edit (QLineEdit): Input field for the password.
        pass_edit_repeat (QLineEdit): Input field to confirm the password.
    """

    # === Signals ===
    registration_btn_clicked = pyqtSignal(str, str, str, str)
    switch_to_log_btn_clicked = pyqtSignal()
    return_to_home = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("RegisterPage")
        self.setWindowTitle("xGoalPro - Register")

        self.login_btn = QPushButton()
        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.pass_edit = QLineEdit()
        self.pass_edit_repeat = QLineEdit()

        self.__init_ui()
        self.__load_stylesheet()

    # === Keyboard event for Enter key ===
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.attempt_register()

    def attempt_register(self):
        username = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.pass_edit.text().strip()
        confirm_password = self.pass_edit_repeat.text().strip()
        self.registration_btn_clicked.emit(username, email, password, confirm_password)

    def clear_form(self):
        self.name_edit.clear()
        self.email_edit.clear()
        self.pass_edit.clear()
        self.pass_edit_repeat.clear()

    def __init_ui(self):
        # === Root layout ===
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(80, 50, 80, 50)
        root_layout.setSpacing(20)

        # === Top bar (home button only) ===
        top_bar = QHBoxLayout()
        top_bar.setAlignment(Qt.AlignLeft)

        home_button = QPushButton("🏠 Home")
        home_button.setObjectName("homeButton")
        home_button.clicked.connect(lambda: self.return_to_home.emit())
        top_bar.addWidget(home_button)

        root_layout.addLayout(top_bar)

        # === Main centered content ===
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
        title = QLabel("Create an Account")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sub_title = QLabel("Join the xGoalPro community")
        sub_title.setObjectName("subTitleLabel")
        sub_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(sub_title)

        # === Form layout ===
        form_layout = QFormLayout()
        form_layout.setFormAlignment(Qt.AlignCenter)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(15)

        self.name_edit.setPlaceholderText("Enter your username")
        self.name_edit.setObjectName("inputField")
        form_layout.addRow(self.name_edit)

        self.email_edit.setPlaceholderText("Enter your email")
        self.email_edit.setObjectName("inputField")
        form_layout.addRow(self.email_edit)

        self.pass_edit.setPlaceholderText("Enter your password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setObjectName("inputField")
        self.pass_edit.setToolTip("Username must be at least 3 characters.\n"
                                  "Username must be at most 20 characters.\n"
                                  "Username can only contain letters and numbers.\n"
                                  "Password must be at least 8 characters.\n"
                                  "Password must contain a lowercase letter.\n"
                                  "Password must contain an uppercase letter.\n"
                                  "Password must contain a number.\n"
                                  "Password must contain a special character.")
        form_layout.addRow(self.pass_edit)

        self.pass_edit_repeat.setPlaceholderText("Confirm your password")
        self.pass_edit_repeat.setEchoMode(QLineEdit.Password)
        self.pass_edit_repeat.setObjectName("inputField")
        self.pass_edit_repeat.setToolTip("Username must be at least 3 characters.\n"
                                  "Username must be at most 20 characters.\n"
                                  "Username can only contain letters and numbers.\n"
                                  "Password must be at least 8 characters.\n"
                                  "Password must contain a lowercase letter.\n"
                                  "Password must contain an uppercase letter.\n"
                                  "Password must contain a number.\n"
                                  "Password must contain a special character.")
        form_layout.addRow(self.pass_edit_repeat)

        main_layout.addLayout(form_layout)

        # === Register button ===
        register_btn = QPushButton("Register")
        register_btn.setObjectName("registerButton")
        register_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        register_btn.clicked.connect(self.attempt_register)
        main_layout.addWidget(register_btn, alignment=Qt.AlignCenter)

        # === Login redirect section ===
        login_layout = QHBoxLayout()
        login_layout.setAlignment(Qt.AlignCenter)

        login_label = QLabel("Already have an account?")
        login_label.setObjectName("loginLabel")
        self.login_btn = QPushButton("Log in")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.clicked.connect(lambda: self.switch_to_log_btn_clicked.emit())

        login_layout.addWidget(login_label)
        login_layout.addWidget(self.login_btn)
        main_layout.addLayout(login_layout)

        # Add main layout to root layout
        root_layout.addLayout(main_layout)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/register_page.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
