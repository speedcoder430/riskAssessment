from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel
from app.utils.scrapers.hithorizons import scrape_hithorizons  # Import the scraper
from app.utils.verifyToken import verify_token
from typing import List
import logging

# Initialize FastAPI router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# Define ScrapeRequest model to parse the request body
class ScrapeRequest(BaseModel):
    links: List[str]

# Scrape function to handle scraping of links
@router.post("/api/scrape/company", status_code=status.HTTP_200_OK)
async def scrape(request: ScrapeRequest, authorization: str = Header(...)):
    await verify_token(authorization)
    """Scrapes the given URLs and extracts company data from www.hithorizons.com."""
    company_data = {}

    for url in request.links:
        try:
            # Use the hithorizons scraper for scraping
            if "www.hithorizons.com" in url:
                result_data = await scrape_hithorizons(url)

                # Add the scraped company data to the list
                company_data = result_data

        except HTTPException as e:
            # Handle HTTP errors explicitly
            logger.error(f"HTTP error occurred while processing {url}: {e.detail}")
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error occurred while processing {url}: {e}")

    # Return company data instead of search result links
    return company_data
