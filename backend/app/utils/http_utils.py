import httpx
from fastapi import HTTPException, status
import logging

# Initialize logger
logger = logging.getLogger(__name__)


async def fetch_html(url: str):
    """Fetches HTML content from a given URL."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Will raise an HTTPStatusError for bad responses
            return response.text
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error for {url}: {e}")
        raise HTTPException(
            status_code=e.response.status_code, detail=f"Failed to fetch {url}"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error for {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error fetching {url}",
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching {url}",
        )
