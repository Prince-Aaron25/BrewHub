from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from database import transaction
from models.user import from_row
from repositories.queries import one, insert
from services.common import text_value, email_value

HASHER = PasswordHasher()


def password_value(password):
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        raise ValueError("Password must contain 8 to 128 characters.")
    return password


def verify(stored, password):
    try:
        return HASHER.verify(stored, password)
    except (VerificationError, InvalidHashError, TypeError):
        return False


class AuthService:
    def register(self, name, email, phone, password):
        name = text_value(name, "Full name", 100)
        email = email_value(email)
        phone = text_value(phone, "Phone", 20, False)
        hashed = HASHER.hash(password_value(password))
        with transaction(write=True) as cur:
            if one(cur, "SELECT user_id FROM users WHERE email=%s", (email,)):
                raise ValueError("That email is already registered.")
            return insert(cur, """INSERT INTO users(full_name,email,phone,password,role,status)
                VALUES(%s,%s,%s,%s,'customer','active')""", (name, email, phone, hashed))

    def login(self, email, password):
        email = email_value(email)
        if not password or len(password) > 128:
            raise ValueError("Enter your password.")
        with transaction() as cur:
            row = one(cur, "SELECT * FROM users WHERE email=%s", (email,))
            if not row or not verify(row["password"], password):
                raise ValueError("Incorrect email or password. Legacy accounts may need a password reset.")
            if row["status"] != "active":
                raise ValueError("This account is inactive. Contact the administrator.")
            return from_row(row)

