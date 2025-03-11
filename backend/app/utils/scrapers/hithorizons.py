import httpx
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from fastapi import HTTPException
import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

async def fetch_html(url: str) -> str:
    """Fetches HTML content from a given URL."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Will raise an HTTPStatusError for bad responses
            return response.text
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error for {url}: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch {url}")
    except httpx.RequestError as e:
        logger.error(f"Request error for {url}: {e}")
        raise HTTPException(status_code=503, detail=f"Error fetching {url}")
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching {url}")


async def extract_coordinates_from_iframe(iframe: str) -> Optional[Dict[str, str]]:
    """Extracts latitude and longitude from an iframe's src URL."""
    if "q=" in iframe:
        iframe_src = iframe.split("q=")[1]
        logger.info("iframe" + iframe_src)
        lat_long = iframe_src.split("%2c+")  # Extract only the part before the next parameter
        latitude = lat_long[0]
        longitude = lat_long[1]
        logger.info(f"Coordinates extracted: Latitude: {latitude}, Longitude: {longitude}")
        return {"latitude": latitude, "longitude": longitude}
    return None


async def scrape_company_data(company_url: str) -> Dict[str, Optional[str]]:
    """Fetch company data from the company's page."""
    html = await fetch_html(company_url)
    tree = HTMLParser(html)

    # Step 1: Get latitude and longitude from iframe
    iframe = tree.css("iframe")
    coordinates = None
    if iframe:
        iframe_src = iframe[0].attributes.get("src", "")
        logger.info(f"Iframe src: {iframe_src}")
        coordinates = await extract_coordinates_from_iframe(iframe_src)

    # Step 2: Scrape company info from <ul class="overview-data-1">
    company_info = {
        "name": "",
        "address": "",
        "postal_code": "",
        "phone": [],
        "email": "",
        "website": "",
        "activity_code_description": "",
        "year": "",
        "employees": "",
        "latitude": "",
        "longitude": "",
    }

    company_info_ul = tree.css("ul.overview-data-1")
    if company_info_ul:
        for li in company_info_ul[0].css("li"):
            strong_tag = li.css("strong")
            span_tag = li.css("span")
            if strong_tag and span_tag:
                key = strong_tag[0].text(strip=True)
                value = span_tag[0].text(strip=True)
                if key == "Name":
                    company_info["name"] = value
                elif key == "Address":
                    company_info["address"] = value
                    # Extract postal code from the address
                    postal_code_match = re.search(r"\d{4}-\d{3}", value)
                    if postal_code_match:
                        company_info["postal_code"] = postal_code_match.group(0)
                elif key == "Est. of Ownership":
                    company_info["year"] = value
                elif key == "Phone":
                    # Avoid adding empty values
                    if value and value not in company_info["phone"]:
                        company_info["phone"].append(value)
                elif key == "Email":
                    company_info["email"] = value
                elif key == "Website":
                    company_info["website"] = value
                elif key == "Activity Code Description":
                    company_info["activity_code_description"] = value
                elif key == "Employees":
                    company_info["employees"] = value

    # Step 3: Add coordinates to the company_info dictionary if found
    if coordinates:
        company_info["latitude"] = coordinates["latitude"]
        company_info["longitude"] = coordinates["longitude"]

    return company_info


async def scrape_hithorizons(url: str) -> List[Dict[str, Optional[str]]]:
    """Scrape the company data from the provided URL, assuming there is a single result link."""
    # Step 1: Fetch the page with the search result link
    html = await fetch_html(url)
    tree = HTMLParser(html)

    # Step 2: Extract the search result link (since there's only one)
    search_result_link = None
    for node in tree.css("a.search-result"):
        search_result_link = node.attributes.get("href")
        break  # Since there's only one, we can stop after finding it

    if not search_result_link:
        raise HTTPException(status_code=404, detail="No search result link found")

    # Step 3: Scrape the company data from the link
    company_url = urljoin(url, search_result_link)  # Ensure full URL
    logger.info(f"Scraping company data from {company_url}")
    data = await scrape_company_data(company_url)

    return {"company_data": data}  # Return as a list of dictionaries

