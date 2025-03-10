from fastapi import FastAPI
from app.api.auth.signIn import router as signin_router
from app.api.auth.signUp import router as signup_router
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

app.include_router(signin_router)
app.include_router(signup_router)


@app.get("/")
def read_root():
    logging.info("App is started correctly!")
    return {"message": "Welcome to the Risk Assessment API"}
