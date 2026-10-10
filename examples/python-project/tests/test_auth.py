from app.auth import AuthError, AuthService
from app.models import UserRepository
from app.security import verify_token


def test_register_and_login():
    users = UserRepository()
    auth = AuthService(users)

    auth.register("alice@example.com", "s3cret")
    token = auth.login("alice@example.com", "s3cret")

    user_id = verify_token(token)
    assert user_id is not None


def test_login_with_wrong_password_fails():
    users = UserRepository()
    auth = AuthService(users)
    auth.register("alice@example.com", "s3cret")

    try:
        auth.login("alice@example.com", "wrong")
        assert False, "expected AuthError"
    except AuthError:
        pass


def test_duplicate_registration_fails():
    users = UserRepository()
    auth = AuthService(users)
    auth.register("alice@example.com", "s3cret")

    try:
        auth.register("alice@example.com", "other")
        assert False, "expected AuthError"
    except AuthError:
        pass
