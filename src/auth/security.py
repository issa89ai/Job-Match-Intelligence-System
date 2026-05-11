from __future__ import annotations


# =========================================================
# Standard Library Imports
# =========================================================

# Date/time utilities for token expiration.
from datetime import datetime, timedelta, timezone

# Optional type hints.
from typing import Optional


# =========================================================
# JWT Library
# =========================================================

# JWTError:
# catches invalid/expired tokens.
#
# jwt:
# encodes and decodes JWT tokens.
from jose import JWTError, jwt


# =========================================================
# Password Hashing
# =========================================================

# CryptContext manages hashing algorithms.
from passlib.context import CryptContext


# =========================================================
# JWT Configuration
# =========================================================

# Secret key used to sign JWT tokens.
#
# VERY IMPORTANT:
# In production this should come from:
# environment variables / secret manager.
SECRET_KEY = "change_this_before_real_deployment"


# JWT signing algorithm.
ALGORITHM = "HS256"


# Default token expiration:
# 60 minutes × 24 = 24 hours
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# =========================================================
# Password Hashing Context
# =========================================================

# Configure bcrypt hashing algorithm.
pwd_context = CryptContext(

    # Hashing algorithm.
    schemes=["bcrypt"],

    # Auto-upgrade deprecated hashes if needed.
    deprecated="auto",
)


# =========================================================
# Password Hashing
# =========================================================

def hash_password(password: str) -> str:
    """
    Convert plain-text password
    into secure bcrypt hash.
    """

    return pwd_context.hash(password)


# =========================================================
# Password Verification
# =========================================================

def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """
    Compare plain password
    against stored hash.
    """

    return pwd_context.verify(
        plain_password,
        password_hash,
    )


# =========================================================
# JWT Token Creation
# =========================================================

def create_access_token(
    subject: str,
    expires_minutes: Optional[int] = None,
) -> str:
    """
    Generate JWT access token.

    subject:
        usually user email.

    expires_minutes:
        optional custom expiration.
    """

    # Calculate expiration timestamp.
    expire = datetime.now(timezone.utc) + timedelta(

        minutes=(
            expires_minutes
            or ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    # JWT payload.
    payload = {

        # Subject:
        # identifies user.
        "sub": subject,

        # Expiration time.
        "exp": expire,
    }

    # Encode signed JWT token.
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# =========================================================
# JWT Token Validation
# =========================================================

def decode_access_token(
    token: str,
) -> Optional[str]:
    """
    Validate JWT token
    and return subject (email).

    Returns:
        subject string if valid
        None if invalid/expired
    """

    try:

        # Decode token.
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        # Extract subject/email.
        subject = payload.get("sub")

        return subject

    except JWTError:

        # Invalid token.
        return None