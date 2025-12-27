"""Tests for HMAC signature verification."""

import base64
import hashlib
import hmac

import pytest

from src.teams.receiver.hmac import (
    HMACVerificationError,
    HMACVerifier,
    create_verifier,
)


class TestHMACVerifier:
    """Tests for HMACVerifier class."""

    @pytest.fixture
    def valid_secret(self):
        """A valid Base64-encoded secret."""
        return base64.b64encode(b"test-secret-key").decode()

    @pytest.fixture
    def verifier(self, valid_secret):
        """Create a verifier with valid secret."""
        return HMACVerifier(valid_secret)

    def _compute_signature(self, secret: str, body: bytes) -> str:
        """Helper to compute HMAC signature."""
        secret_bytes = base64.b64decode(secret)
        signature = hmac.new(secret_bytes, body, hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def test_init_with_valid_secret(self, valid_secret):
        """Test initialization with valid Base64 secret."""
        verifier = HMACVerifier(valid_secret)
        assert verifier.is_configured() is True

    def test_init_with_empty_secret_raises(self):
        """Test that empty secret raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            HMACVerifier("")

    def test_init_with_invalid_base64_raises(self):
        """Test that invalid Base64 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid Base64"):
            HMACVerifier("not-valid-base64!!!")

    def test_verify_valid_signature(self, verifier, valid_secret):
        """Test verification with valid signature."""
        body = b'{"message": "hello"}'
        signature = self._compute_signature(valid_secret, body)
        auth_header = f"HMAC {signature}"

        result = verifier.verify(auth_header, body)
        assert result is True

    def test_verify_missing_header_raises(self, verifier):
        """Test that missing header raises error."""
        with pytest.raises(HMACVerificationError, match="Missing Authorization"):
            verifier.verify(None, b"body")

    def test_verify_empty_header_raises(self, verifier):
        """Test that empty header raises error."""
        with pytest.raises(HMACVerificationError, match="Missing Authorization"):
            verifier.verify("", b"body")

    def test_verify_invalid_format_raises(self, verifier):
        """Test that invalid header format raises error."""
        with pytest.raises(HMACVerificationError, match="Invalid Authorization header"):
            verifier.verify("Bearer token", b"body")

    def test_verify_wrong_signature_raises(self, verifier):
        """Test that wrong signature raises error."""
        auth_header = "HMAC wrongsignature"

        with pytest.raises(HMACVerificationError, match="Invalid HMAC signature"):
            verifier.verify(auth_header, b"body")

    def test_verify_case_insensitive_hmac(self, verifier, valid_secret):
        """Test that HMAC prefix is case-insensitive."""
        body = b"test"
        signature = self._compute_signature(valid_secret, body)

        # Lowercase should work
        result = verifier.verify(f"hmac {signature}", body)
        assert result is True

    def test_verify_different_body_fails(self, verifier, valid_secret):
        """Test that signature for different body fails."""
        original_body = b"original"
        signature = self._compute_signature(valid_secret, original_body)
        auth_header = f"HMAC {signature}"

        with pytest.raises(HMACVerificationError, match="Invalid HMAC signature"):
            verifier.verify(auth_header, b"different")

    def test_is_configured(self, verifier):
        """Test is_configured returns True when secret is set."""
        assert verifier.is_configured() is True


class TestCreateVerifier:
    """Tests for create_verifier factory function."""

    def test_create_with_valid_secret(self):
        """Test creating verifier with valid secret."""
        secret = base64.b64encode(b"secret").decode()
        verifier = create_verifier(secret)

        assert verifier is not None
        assert isinstance(verifier, HMACVerifier)

    def test_create_with_none_returns_none(self):
        """Test that None secret returns None."""
        verifier = create_verifier(None)
        assert verifier is None

    def test_create_with_empty_returns_none(self):
        """Test that empty secret returns None."""
        verifier = create_verifier("")
        assert verifier is None

    def test_create_with_invalid_secret_returns_none(self):
        """Test that invalid Base64 secret returns None."""
        verifier = create_verifier("invalid!!!")
        assert verifier is None
