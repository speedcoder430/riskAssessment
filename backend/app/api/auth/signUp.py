from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.core.client import supabase
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest):
    try:
        if len(request.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long.",
            )

        response = supabase.auth.sign_up(
            {"email": request.email, "password": request.password}
        )

        if "error" in response:
            logger.warning(
                f"Signup failed for {request.email}: {response['error']['message']}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response["error"]["message"],
            )

        logger.info(f"User created successfully: {request.email}")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
        }

    except ValueError as e:
        logger.error(f"ValueError during sign-up: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request data."
        )

    except ConnectionError:
        logger.error("Failed to connect to Supabase service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )

    except Exception as e:
        logger.error(f"Unexpected error during sign-up: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )
