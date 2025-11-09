import bcrypt

from shared.security.password import hash_password, verify_password


def test_hash_password_returns_valid_bcrypt_hash():
    """
    Test that `hash_password()` generates a valid bcrypt hash.

    Steps:
      1. Call `hash_password()` with a known password.
      2. Ensure it returns a string (decoded UTF-8).
      3. Ensure bcrypt recognizes it as a valid hash.
    """
    password = "SuperSecret123!"
    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def test_verify_password_returns_true_for_valid_hash():
    """
    Test that `verify_password()` returns True when hash matches.
    """
    password = "test123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_returns_false_for_invalid_password():
    """
    Test that `verify_password()` returns False when password is incorrect.
    """
    password = "correct_password"
    hashed = hash_password(password)

    assert verify_password("wrong_password", hashed) is False


def test_verify_password_handles_invalid_hash_gracefully(monkeypatch):
    """
    Test that `verify_password()` returns False if bcrypt.checkpw raises an exception.
    """

    def raise_error(*args, **kwargs):
        raise ValueError("bcrypt failed")

    monkeypatch.setattr("bcrypt.checkpw", raise_error)

    result = verify_password("pass", "not_a_real_hash")
    assert result is False


def test_hash_password_produces_different_hashes_each_time():
    """
    Test that hashing the same password twice produces different hashes due to salt.
    """
    password = "repeatable"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)
