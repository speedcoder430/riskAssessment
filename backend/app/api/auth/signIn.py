from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.core.client import supabase
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/api/auth/signin", status_code=status.HTTP_200_OK)
async def signin(request: SignInRequest):
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password}
        )

        if not response or not response.session.access_token:
            logger.warning(f"Failed login attempt for email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Invalid email or password",
            )

        logger.info(f"User signed in successfully: {request.email}")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
        }

    except ValueError as e:
        logger.error(f"ValueError during sign-in: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request data"
        )

    except ConnectionError:
        logger.error("Failed to connect to Supabase service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="Service temporarily unavailable. Please try again later.",
        )

    except Exception as e:
        logger.error(f"Unexpected error during sign-in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=f"{e}",
        )
