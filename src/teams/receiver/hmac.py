"""HMAC signature verification for Teams Outgoing Webhooks.

Microsoft Teams Outgoing Webhooks sign requests using HMAC-SHA256.
The signature is sent in the Authorization header as: HMAC <base64-signature>
"""

import base64
import hashlib
import hmac

import structlog

logger = structlog.get_logger(__name__)


class HMACVerificationError(Exception):
    """Raised when HMAC signature verification fails."""

    pass


class HMACVerifier:
    """Verifies HMAC signatures from Teams Outgoing Webhooks.

    Teams signs the request body using HMAC-SHA256 with a shared secret.
    The secret is provided when creating the Outgoing Webhook in Teams
    and is Base64-encoded.

    Example:
        verifier = HMACVerifier(secret="your-base64-secret")

        # In your webhook handler:
        auth_header = request.headers.get("Authorization")
        body = await request.body()

        if verifier.verify(auth_header, body):
            # Process the message
            pass
    """

    def __init__(self, secret: str):
        """Initialize the verifier with the shared secret.

        Args:
            secret: Base64-encoded HMAC secret from Teams Outgoing Webhook
        """
        if not secret:
            raise ValueError("HMAC secret cannot be empty")

        try:
            self._secret_bytes = base64.b64decode(secret)
        except Exception as e:
            raise ValueError(f"Invalid Base64 secret: {e}") from e

        self._secret = secret

    def _compute_signature(self, body: bytes) -> str:
        """Compute HMAC-SHA256 signature for the request body.

        Args:
            body: Raw request body bytes

        Returns:
            Base64-encoded signature string
        """
        signature = hmac.new(
            self._secret_bytes,
            body,
            hashlib.sha256,
        ).digest()
        return base64.b64encode(signature).decode("utf-8")

    def verify(self, auth_header: str | None, body: bytes) -> bool:
        """Verify the HMAC signature from the Authorization header.

        Args:
            auth_header: The Authorization header value (e.g., "HMAC abc123...")
            body: Raw request body bytes

        Returns:
            True if signature is valid

        Raises:
            HMACVerificationError: If verification fails
        """
        if not auth_header:
            logger.warning("hmac_verification_failed", reason="missing_header")
            raise HMACVerificationError("Missing Authorization header")

        # Parse the Authorization header
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].upper() != "HMAC":
            logger.warning(
                "hmac_verification_failed",
                reason="invalid_header_format",
                header_prefix=parts[0] if parts else None,
            )
            raise HMACVerificationError("Invalid Authorization header format")

        provided_signature = parts[1]
        computed_signature = self._compute_signature(body)

        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(provided_signature, computed_signature):
            logger.warning(
                "hmac_verification_failed",
                reason="signature_mismatch",
            )
            raise HMACVerificationError("Invalid HMAC signature")

        logger.debug("hmac_verification_success")
        return True

    def is_configured(self) -> bool:
        """Check if the verifier has a valid secret configured."""
        return bool(self._secret_bytes)


def create_verifier(secret: str | None) -> HMACVerifier | None:
    """Create an HMAC verifier if secret is provided.

    Args:
        secret: Base64-encoded HMAC secret, or None

    Returns:
        HMACVerifier instance or None if no secret provided
    """
    # Check for empty or placeholder values
    if not secret or secret.upper() in ("DISABLED", "NONE", "OFF", "FALSE"):
        logger.warning(
            "hmac_verifier_disabled",
            reason="no_secret_configured" if not secret else "explicitly_disabled",
        )
        return None

    try:
        return HMACVerifier(secret)
    except ValueError as e:
        logger.error("hmac_verifier_creation_failed", error=str(e))
        return None
