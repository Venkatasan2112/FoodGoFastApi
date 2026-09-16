from fastapi import FastAPI

from app.routers import users, auth


app = FastAPI(title="FoodGo API", version="1.0.0")


app.include_router(users.router)
app.include_router(auth.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "FoodGo API"}