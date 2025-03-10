import os
import requests
from fastapi import APIRouter, HTTPException, status, Header
from app.utils.verifyToken import verify_token
from app.utils.logging import get_logger
from cachetools import TTLCache

router = APIRouter()
logger = get_logger(__name__)

GOOGLE_SEARCH_URL = os.getenv("GOOGLE_SEARCH_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

cache = TTLCache(maxsize=100, ttl=300)


@router.get("/api/search/company/{company_id}")
async def search_company(company_id: str, authorization: str = Header(...)):
    await verify_token(authorization)

    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        logger.error("Google API key or Search Engine ID is missing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: Missing API keys.",
        )

    if company_id in cache:
        logger.info(f"Cache hit for company ID: {company_id}")
        return cache[company_id]

    search_url = (
        f"{GOOGLE_SEARCH_URL}"
        f"?q={company_id}"
        f"&cx={SEARCH_ENGINE_ID}"
        f"&key={GOOGLE_API_KEY}"
    )

    try:
        response = requests.get(search_url)
        response.raise_for_status()

        search_results = response.json()

        if "items" not in search_results:
            logger.warning(f"No search results found for company ID: {company_id}")
            return {"message": "No results found", "company_id": company_id}

        links = [item["link"] for item in search_results["items"]]

        cache[company_id] = links

        return links

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching search results: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from Google Search API.",
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
