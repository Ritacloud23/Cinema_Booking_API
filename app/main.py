from fastapi import FastAPI

app = FastAPI(title="ScreenHive API")



@app.get("/")
def home():
    return {"message": "ScreenHive API is running"}
