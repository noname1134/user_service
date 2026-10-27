from fastapi import FastAPI

from controllers import router


app = FastAPI()
app.include_router(router)


@app.get("/")
def root():
    return {"message": "User service is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}