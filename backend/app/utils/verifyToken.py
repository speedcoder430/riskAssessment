from fastapi import HTTPException, Header, status
from app.utils.logging import get_logger
from app.core.client import supabase

logger = get_logger(__name__)


async def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        logger.error("Invalid token format.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    token = authorization.split("Bearer ")[1]

    try:
        response = supabase.auth.get_user(token)
        print(f"{response.user.json()}")
        if not response.user.email:
            logger.error("Unauthorized access attempt detected.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired token",
            )

        logger.info(f"Token verified for user: {response.user.email}")
        return response.user.email

    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token verification failed",
        )
