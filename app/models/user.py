"""
This module defines the User model, which is responsible for handling
user authentication, authorization, and user-specific data such as associated projects.
It integrates with Flask-Login for session management and uses `itsdangerous`
for generating and verifying security tokens for email confirmation and password resets.
"""

from app import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash # Added generate_password_hash for completeness, though not directly used in this file's methods.
from itsdangerous import URLSafeTimedSerializer

class User(db.Model, UserMixin):
    """
    Represents an application user.

    This model stores user information including credentials for login,
    personal details, administrative status, and relationships to other
    models like Projects. It includes methods for password hashing,
    and token generation/verification for email confirmation and password resets.

    Attributes:
        id (int): Primary key for the user.
        name (str): User's full name.
        email (str): User's email address (unique, required). Used for login.
        is_admin (bool): Flag indicating if the user has administrative privileges. Defaults to False.
        password_hash (str): Hashed version of the user's password.
        projects (relationship): SQLAlchemy relationship to 'Project' model, linking users to their projects.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128)) # User's display name
    email = db.Column(db.String(128), unique=True, nullable=False) # User's email, used for login and communication
    is_admin = db.Column(db.Boolean, default=False) # True if the user has admin rights, False otherwise
    password_hash = db.Column(db.String(128)) # Stores the hashed password for security

    # Relationship to Project model: A user can have multiple projects.
    # `cascade='all, delete-orphan'` means that if a User is deleted,
    # all their associated Project records will also be deleted.
    projects = db.relationship('Project', back_populates='user', cascade='all, delete-orphan')

    # Note: A set_password(self, password) method would typically be here to generate the password_hash
    # using generate_password_hash(password) from werkzeug.security.

    def check_password(self, password_hash, password):
        """
        Verify a given plaintext password against the stored password hash.

        Args:
            password_hash (str): The stored password hash to check against.
                                 (Note: Typically this would be self.password_hash)
            password (str): The plaintext password to verify.

        Returns:
            bool: True if the password matches the hash, False otherwise.
        """
        # It's more common to see this as: return check_password_hash(self.password_hash, password)
        return check_password_hash(password_hash, password)

    @staticmethod
    def generate_confirmation_token(email, secret_key, salt):
        """
        Generate a time-sensitive token for email confirmation.

        Uses `itsdangerous.URLSafeTimedSerializer` to create a secure,
        URL-safe token that embeds the email and has an expiration time.

        Args:
            email (str): The email address to include in the token.
            secret_key (str): The secret key used for signing the token.
            salt (str): A salt value to namespace the token, enhancing security.

        Returns:
            str: The generated confirmation token.
        """
        serializer = URLSafeTimedSerializer(secret_key)
        return serializer.dumps(email, salt=salt)

    @staticmethod
    def verify_confirmation_token(token, secret_key, salt, expiration=3600):
        """
        Verify an email confirmation token.

        Uses `itsdangerous.URLSafeTimedSerializer` to decode the token and check
        its validity and expiration.

        Args:
            token (str): The confirmation token to verify.
            secret_key (str): The secret key used for signing the token.
            salt (str): The salt value used when the token was generated.
            expiration (int): The maximum age of the token in seconds (default: 3600 seconds = 1 hour).

        Returns:
            str or None: The email address if the token is valid and not expired, otherwise None.
        """
        serializer = URLSafeTimedSerializer(secret_key)
        try:
            email = serializer.loads(
                token,
                salt=salt,
                max_age=expiration # Checks if the token has expired
            )
            return email
        except Exception: # Catches various exceptions from itsdangerous (e.g., SignatureExpired, BadSignature)
            return None

    @staticmethod
    def generate_reset_token(email, secret_key, salt):
        """
        Generate a time-sensitive token for password reset requests.

        Uses `itsdangerous.URLSafeTimedSerializer` to create a secure token.
        A different salt suffix ('reset') is used to distinguish password reset
        tokens from email confirmation tokens.

        Args:
            email (str): The email address for which to reset the password.
            secret_key (str): The secret key used for signing the token.
            salt (str): The base salt value. A suffix will be added for password reset.

        Returns:
            str: The generated password reset token.
        """
        serializer = URLSafeTimedSerializer(secret_key)
        return serializer.dumps(email, salt=salt + 'reset') # Using a different salt for reset tokens

    @staticmethod
    def verify_reset_token(token, secret_key, salt, expiration=3600):
        """
        Verify a password reset token.

        Uses `itsdangerous.URLSafeTimedSerializer` to decode the token and check
        its validity and expiration. Uses the 'reset' suffixed salt.

        Args:
            token (str): The password reset token to verify.
            secret_key (str): The secret key used for signing the token.
            salt (str): The base salt value used when the token was generated.
            expiration (int): The maximum age of the token in seconds (default: 3600 seconds = 1 hour).

        Returns:
            str or None: The email address if the token is valid and not expired, otherwise None.
        """
        serializer = URLSafeTimedSerializer(secret_key)
        try:
            email = serializer.loads(
                token,
                salt=salt + 'reset', # Using the specific salt for reset tokens
                max_age=expiration
            )
            return email
        except Exception: # Catches errors like token expiration or tampering
            return None
