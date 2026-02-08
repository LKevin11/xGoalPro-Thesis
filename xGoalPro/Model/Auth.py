import asyncio
import hashlib
import secrets
import binascii
from typing import Tuple, List
import re
from Persistence.StorageInterface import IUserStorage


class IAuthModel:
    """Interface for authentication models handling user registration and login."""

    async def register(self, username: str, email: str, password: str, confirm_password: str) -> Tuple[bool, List[str]]:
        """Register a new user.

        Args:
            username (str): Desired username.
            email (str): User's email address.
            password (str): User's password.
            confirm_password (str): Password confirmation.

        Returns:
            Tuple[bool, List[str]]: A tuple where the first element indicates success,
            and the second element contains either the username or a list of error messages.
        """
        ...

    async def login(self, username: str, password: str) -> Tuple[bool, List[str]]:
        """Authenticate a user.

        Args:
            username (str): The username of the user attempting to log in.
            password (str): The plaintext password for verification.

        Returns:
            Tuple[bool, List[str]]: A tuple where the first element indicates success,
            and the second element contains either user details (username and ID) or a list of error messages.
        """
        ...


EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _is_valid_email(email: str) -> bool:
    """Check if an email address is valid using a regex pattern.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email is valid, False otherwise.
    """
    return re.match(EMAIL_REGEX, email) is not None


class AuthModel(IAuthModel):
    """Concrete implementation of IAuthModel using secure password hashing.

    Attributes:
        __storage (IUserStorage): Interface for persistence layer operations.
        __errors (List[str]): List of error messages during operations.
        __hash_iterations (int): Number of iterations for PBKDF2 hashing.
        __hash_algorithm (str): Hash algorithm used in PBKDF2.
        __salt_length (int): Length of the generated salt in bytes.
        __hash_length (int): Length of the derived password hash in bytes.
    """

    def __init__(self, storage):
        """Initialize the AuthModel with a storage backend.

        Args:
            storage (IUserStorage): The storage interface for user data operations.
        """
        self.__storage: IUserStorage = storage
        self.__errors: List[str] = []
        # Security parameters (can be configurable)
        self.__hash_iterations: int = 210_000  # OWASP 2021 recommendation for PBKDF2-HMAC-SHA256
        self.__hash_algorithm: str = 'sha256'
        self.__salt_length: int = 32  # bytes
        self.__hash_length: int = 64  # bytes

    async def register(self, username: str, email: str, password: str, confirm_password: str) -> Tuple[bool, List[str]]:
        """Register a new user with validation and secure password hashing.

        Validates the username, password, and email, confirms the password,
        generates a cryptographically secure salt, hashes the password using PBKDF2,
        and stores the user in the persistence layer.

        Args:
            username (str): Desired username.
            email (str): User's email address.
            password (str): User's password.
            confirm_password (str): Password confirmation.

        Returns:
            Tuple[bool, List[str]]: (success, data)
                - success (bool): True if registration was successful.
                - data (List[str]): Either the registered username or a list of error messages.
        """
        await self._clear_errors()
        await self._validate_credentials(username, password, email)
        self._confirm_password(password, confirm_password)

        if self.__errors:
            return False, self.__errors

        try:
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)

            if await self.__storage.user_exists(username):
                self.__errors.append("Username already exists")
                return False, self.__errors

            await self.__storage.create_user(username, email, salt, password_hash)
            return True, [username]

        except Exception as e:
            self.__errors.append(f"Registration failed: {str(e)}")
            return False, self.__errors

    async def login(self, username: str, password: str) -> Tuple[bool, List[str]]:
        """Authenticate a user by verifying the password hash.

        Args:
            username (str): The username to authenticate.
            password (str): The plaintext password to verify.

        Returns:
            Tuple[bool, List[str]]: (success, data)
                - success (bool): True if authentication was successful.
                - data (List[str]): Either [username, user_id] on success, or a list of error messages.
        """
        await self._clear_errors()

        try:
            user = await self.__storage.get_user(username)

            if not user:
                self.__errors.append("User does not exist!")
                return False, self.__errors

            stored_salt = user['password_salt']
            stored_hash = user['password_hash']
            computed_hash = self._hash_password(password, stored_salt)

            if not secrets.compare_digest(computed_hash, stored_hash):
                self.__errors.append("Invalid credentials")
                return False, self.__errors

            return True, [username, user["id"]]
        except Exception as e:
            self.__errors.append(f"Login failed: {str(e)}")
            return False, self.__errors

    def _generate_salt(self) -> str:
        """Generate a cryptographically secure salt.

        Returns:
            str: Hexadecimal representation of the salt.
        """
        return secrets.token_hex(self.__salt_length)

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash a password using PBKDF2-HMAC with a given salt.

        Args:
            password (str): The plaintext password.
            salt (str): The salt to use in hashing.

        Returns:
            str: Hexadecimal representation of the derived password hash.
        """
        derived_key = hashlib.pbkdf2_hmac(
            self.__hash_algorithm,
            password.encode('utf-8'),
            salt.encode('utf-8'),
            self.__hash_iterations,
            dklen=self.__hash_length
        )
        return binascii.hexlify(derived_key).decode('utf-8')

    async def _validate_credentials(self, username: str, password: str, email: str) -> None:
        """Validate username, password, and email against security rules.

        Updates self.__errors with any validation issues found.

        Args:
            username (str): Username to validate.
            password (str): Password to validate.
            email (str): Email to validate.
        """
        # Username rules
        if len(username) < 3:
            self.__errors.append("Username must be at least 3 characters.")
        if len(username) > 20:
            self.__errors.append("Username must be at most 20 characters.")
        if not username.isalnum():
            self.__errors.append("Username can only contain letters and numbers.")

        # Password rules
        if len(password) < 8:
            self.__errors.append("Password must be at least 8 characters.")
        if not any(c.islower() for c in password):
            self.__errors.append("Password must contain a lowercase letter.")
        if not any(c.isupper() for c in password):
            self.__errors.append("Password must contain an uppercase letter.")
        if not any(c.isdigit() for c in password):
            self.__errors.append("Password must contain a number.")
        if not any(c in "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~" for c in password):
            self.__errors.append("Password must contain a special character.")

        # Email rules
        if not _is_valid_email(email):
            self.__errors.append("Email is not valid.")

    def _confirm_password(self, password: str, confirm_password: str) -> None:
        """Check if the password and confirmation password match.

        Updates self.__errors if passwords do not match.

        Args:
            password (str): Original password.
            confirm_password (str): Confirmation password.
        """

        if password != confirm_password:
            self.__errors.append("Passwords do not match.")

    async def _clear_errors(self) -> None:
        """Clear the internal error list after a short delay.

        This method is async to simulate potential I/O operations.
        """
        await asyncio.sleep(2)
        self.__errors.clear()
