import os
import requests
from fastapi import APIRouter, HTTPException, status, Response, Header
from pydantic import BaseModel
from cachetools import TTLCache
from app.utils.logging import get_logger
from app.utils.verifyToken import verify_token

router = APIRouter()
logger = get_logger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Cache to store images for 5 minutes (TTL = 300 seconds)
cache = TTLCache(maxsize=100, ttl=300)


class LocationRequest(BaseModel):
    latitude: str
    longitude: str


@router.post("/api/maps/company")
async def get_google_maps_image(
    location: LocationRequest, authorization: str = Header(...)
):
    # Verify the token from the authorization header
    await verify_token(authorization)

    if not GOOGLE_API_KEY:
        logger.error("Google Maps API key is missing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: Missing API key.",
        )

    # Cache key based on latitude and longitude
    cache_key = f"{location.latitude},{location.longitude}"

    # Check if the image is cached
    if cache_key in cache:
        logger.info(f"Cache hit for location: {cache_key}")
        return Response(content=cache[cache_key], media_type="image/png")

    google_maps_url = (
        f"https://maps.googleapis.com/maps/api/staticmap?"
        f"center={location.latitude},{location.longitude}"
        f"&zoom=16&size=640x480&scale=2&maptype=hybrid"
        f"&markers=Center|{location.latitude},{location.longitude}"
        f"&key={GOOGLE_API_KEY}"
    )

    try:
        response = requests.get(google_maps_url)
        response.raise_for_status()

        # Cache the image for future requests
        cache[cache_key] = response.content

        return Response(content=response.content, media_type="image/png")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Google Maps image: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from Google Maps API.",
        )
