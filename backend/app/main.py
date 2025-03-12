from fastapi import FastAPI
from app.api.auth.signIn import router as signin_router
from app.api.auth.signUp import router as signup_router
from app.api.auth.refresh import router as refresh_token_router
from app.api.search.company import router as company_search_router
from app.api.scrape.company import router as scrape_company_router
from app.api.maps.company import router as gmap_image_router
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

app.include_router(signin_router)
app.include_router(signup_router)
app.include_router(refresh_token_router)
app.include_router(company_search_router)
app.include_router(scrape_company_router)
app.include_router(gmap_image_router)


@app.get("/")
def read_root():
    logging.info("App is started correctly!")
    return {"message": "Welcome to the Risk Assessment API"}
