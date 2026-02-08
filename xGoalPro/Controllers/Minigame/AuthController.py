from qasync import asyncSlot
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget

from Persistence.StorageInterface import IUserStorage

from Model.Auth import IAuthModel

from View.Login_Register.Register import RegisterPage
from View.Login_Register.Login import LoginPage
from View.Components.LoadingWidget import LoadingWidget

from ResourcePath import resource_path


class AuthController(QObject):
    """
    Controller responsible for user authentication flow.

    Handles user login and registration interactions between the authentication model,
    persistent storage layer, and the corresponding UI views (Login and Register pages).
    Provides async handling for login and registration requests, manages navigation between
    views, and emits appropriate signals for success, error, or home navigation.

    Signals:
        login_successful (pyqtSignal[str, int]): 
            Emitted when the user logs in successfully, passing the username and user ID.
        registration_successful (pyqtSignal[list]): 
            Emitted when a new user registration is successful, passing success messages.
        error_occurred (pyqtSignal[list]): 
            Emitted when an error occurs during login or registration, passing error messages.
        switch_to_view (pyqtSignal[QWidget]): 
            Emitted to request switching the displayed view.
        return_to_home (pyqtSignal): 
            Emitted to navigate back to the application's home screen.

    Attributes:
        __user_storage (IUserStorage): Interface for user-related persistence operations.
        __auth_model (IAuthModel): The authentication model handling login and registration logic.
        __login_page (LoginPage): The login UI view.
        __register_page (RegisterPage): The registration UI view.
    """


    # Signals
    login_successful: pyqtSignal(str, int) = pyqtSignal(str, int)
    registration_successful: pyqtSignal(list) = pyqtSignal(list)
    error_occurred: pyqtSignal(list) = pyqtSignal(list)
    switch_to_view: pyqtSignal(QWidget) = pyqtSignal(QWidget)
    return_to_home: pyqtSignal = pyqtSignal()

    def __init__(self, storage, model, login_view, register_view):
        """
        Initialize the AuthController with persistence, model, and view components.

        Args:
            storage (IUserStorage): Storage interface for handling user data persistence.
            model (IAuthModel): Authentication model providing login/register functionality.
            login_view (LoginPage): Login view for user credentials input.
            register_view (RegisterPage): Registration view for creating new accounts.
        """
        super().__init__()
        
        # Persistence
        self.__user_storage: IUserStorage = storage

        # Models
        self.__auth_model: IAuthModel = model

        # Views
        self.__login_page: LoginPage = login_view
        self.__register_page: RegisterPage = register_view

        self.__init_connections()

    def switch_to_log(self) -> None:
        """
        Switch to the login view.

        Clears both the login and registration forms before switching to ensure a clean state.
        """
        self.__login_page.clear_form()
        self.__register_page.clear_form()
        self.switch_to_view.emit(self.__login_page)

    def switch_to_reg(self) -> None:
        """
        Switch to the registration view.

        Clears both the login and registration forms before switching to ensure a clean state.
        """
        self.__login_page.clear_form()
        self.__register_page.clear_form()
        self.switch_to_view.emit(self.__register_page)

    async def cleanup(self) -> None:
        """
        Clean up resources and close database connections.

        Closes any active storage connections, deletes UI components, and nullifies references.
        """
        await self.__user_storage.close_connection()

        self.__user_storage = None
        self.__auth_model = None

        self.__register_page.deleteLater()
        self.__login_page.deleteLater()

    def __init_connections(self) -> None:
        """
        Initialize signal-slot connections between views and controller methods.

        Connects UI signals from the login and registration pages to their respective 
        controller slots for login attempts, registration attempts, and navigation.
        """
        self.__login_page.login_btn_clicked.connect(lambda username, password: self.__attempt_login(username, password))
        self.__login_page.switch_to_reg_btn_clicked.connect(self.switch_to_reg)
        self.__login_page.return_to_home.connect(lambda: self.return_to_home.emit())

        self.__register_page.registration_btn_clicked.connect(
            lambda username, email, password, c_password:
            self.__attempt_registration(username, email, password, c_password))
        self.__register_page.switch_to_log_btn_clicked.connect(self.switch_to_log)
        self.__register_page.return_to_home.connect(lambda: self.return_to_home.emit())

    @asyncSlot(str, str)
    async def __attempt_login(self, username: str, password: str) -> None:
        """
        Attempt to log in a user asynchronously.

        Displays a loading widget while performing authentication through the model.
        If successful, emits `login_successful`; otherwise, displays the login page again
        and emits `error_occurred`.

        Args:
            username (str): The entered username.
            password (str): The entered password.
        """
        try:
            loading_widget = LoadingWidget(resource_path("./Assets/loading.gif"), "Logging in ...")
            self.switch_to_view.emit(loading_widget)
            self.__login_page.clear_form()
            await self.__user_storage.initialize_connection()

            success, messages = await self.__auth_model.login(username, password)
            if success:
                self.login_successful.emit(messages[0], messages[1])
            else:
                self.error_occurred.emit(messages)
                self.switch_to_view.emit(self.__login_page)

        except Exception as e:
            await self.cleanup()
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()

    @asyncSlot(str, str, str, str)
    async def __attempt_registration(self, username: str, email: str, password: str, confirm_password: str) -> None:
        """
        Attempt to register a new user asynchronously.

        Displays a loading widget during registration. On success, emits 
        `registration_successful` and returns to the login view. On failure,
        emits `error_occurred` and returns to the registration view.

        Args:
            username (str): Desired username.
            email (str): User email address.
            password (str): Chosen password.
            confirm_password (str): Password confirmation input.
        """
        try:
            loading_widget = LoadingWidget(resource_path("./Assets/loading.gif"), "Creating account ...")
            self.switch_to_view.emit(loading_widget)
            #self.__register_page.clear_form()
            await self.__user_storage.initialize_connection()

            success, messages = await self.__auth_model.register(username, email, password, confirm_password)
            if success:
                self.registration_successful.emit(["Registration successful!"])
                self.switch_to_view.emit(self.__login_page)
            else:
                self.error_occurred.emit(messages)
                self.switch_to_view.emit(self.__register_page)

        except Exception as e:
            await self.cleanup()
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
