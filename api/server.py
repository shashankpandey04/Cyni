from fastapi import Depends, FastAPI

from api.auth import verify_api_key

from .routes.auth import router as auth_router
from .routes.website import router as website_router


def create_app(bot) -> FastAPI:
    app = FastAPI(
        title="CYNI API",
        version="1.0.0",
        dependencies=[Depends(verify_api_key)],
    )

    app.state.bot = bot

    app.include_router(website_router)
    app.include_router(auth_router)

    return app
