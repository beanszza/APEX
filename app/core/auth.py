"""JWT Validation module sharing secret with ms-authentication."""

import logging
import jwt
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def get_current_user_claims(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(security)
) -> dict:
    """Extract and validate JWT token from Bearer header or erp_access_token cookie."""
    settings = get_settings()

    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("erp_access_token") or request.cookies.get("customer_access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required.")

    try:
        payload = jwt.decode(
            token,
            key=settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Flexibly validate audience if required
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError as e:
        logger.warning("JWT validation failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid authentication token.")
