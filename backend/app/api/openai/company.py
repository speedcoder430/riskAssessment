from fastapi import APIRouter, HTTPException, status, File, UploadFile, Header
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from io import BytesIO
from app.utils.logging import get_logger
from app.utils.verifyToken import verify_token
import os
import json
import base64

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

router = APIRouter()

logger = get_logger(__name__)


class RiskResponse(BaseModel):
    location_risk: dict
    sector_specific_risk: dict
    key_takeaways_for_insurers: list


def call_openai_api(image: BytesIO, prompt: str):
    try:
        if image.getbuffer().nbytes == 0:
            raise ValueError("Uploaded image is empty or invalid.")

        b64_image = base64.b64encode(image.read()).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
        )

        if not response.choices:
            raise ValueError("Empty response from OpenAI API.")

        response_text = response.choices[0].message.content
        logger.info(f"Received response from OpenAI: {response_text}")

        try:
            parsed_response = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format from OpenAI: {str(e)}")

        if not isinstance(parsed_response, dict):
            raise ValueError("Response is not a valid JSON object.")

        return parsed_response

    except OpenAIError as e:
        logger.error(f"OpenAI API Error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")

    except ValueError as e:
        logger.error(f"Validation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/api/openai/company", status_code=status.HTTP_200_OK)
async def parse_company_risk(
    company_name: str,
    address: str,
    image: UploadFile = File(...),
    authorization: str = Header(...),
):
    await verify_token(authorization)
    try:
        if not company_name or not address:
            raise HTTPException(
                status_code=400, detail="Company name and address are required."
            )

        image_bytes = await image.read()
        image_data = BytesIO(image_bytes)

        prompt = (
            f"Based on the location of {company_name} at {address}, evaluate the likelihood of various physical risks. For each risk, provide a score from 0 to 5 and list the reasons behind the score. Consider the following risks: - Rising Sea Levels - Droughts - Flooding - Fires - Storms - Heatwaves - Air Pollution. If there are any other relevant risks specific to the location, please include them. Please format your response as a valid JSON object with the following structure:"
            + " {{ 'location_risk': {{'rising_sea_levels': {{'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...]}}, 'droughts': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...] }}, 'flooding': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...] }}, 'fires': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...]}}, 'storms': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...]}}, 'heatwaves': {{ 'score': <score_0_to_5>, 'reason':  ['reason_a', 'reason_b', ...]}}, 'air_pollution': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...]}}, }}, 'sector_specific_risk': {{ 'supply_chain_disruptions': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...]}}, 'regulatory_compliance': {{ 'score': <score_0_to_5>, 'reason':  ['reason_a', 'reason_b', ...]}}, 'market_volatility': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...]}}, 'environmental_concerns': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...]}}, 'credit_financial_risks': {{ 'score': <score_0_to_5>, 'reason': ['reason_a', 'reason_b', ...] }} }}, 'key_takeaways_for_insurers': [ 'key_takeaway_1', 'key_takeaway_2', 'key_takeaway_3', ... ] }}"
        )

        openai_response = call_openai_api(image_data, prompt)

        return RiskResponse(**openai_response)

    except HTTPException as e:
        logger.error(f"Request error: {e.detail}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
