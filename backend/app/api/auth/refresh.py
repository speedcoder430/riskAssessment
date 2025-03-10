from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.core.client import supabase
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/api/auth/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(refresh_token: str):  # Accept the refresh token as a query parameter
    try:
        # Refresh the access token using the provided refresh token
        response = supabase.auth.refresh_session(refresh_token)

        if not response or not response.session.access_token:
            logger.warning(f"Failed to refresh token using refresh token: {refresh_token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        logger.info("Successfully refreshed access token.")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,  # Return the new refresh token
            "token_type": "bearer"
        }

    except ValueError as e:
        logger.error(f"ValueError during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request data"
        )

    except ConnectionError:
        logger.error("Failed to connect to Supabase service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )

    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )
