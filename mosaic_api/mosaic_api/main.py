"""mosaic_api app."""

from mosaic_api import version
from mosaic_api.api.api_v1.api import api_router
from mosaic_api.core import config
import uvicorn

from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

app = FastAPI(
    title=config.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=version,
)


def configure():
    # Set all CORS enabled origins
    if config.BACKEND_CORS_ORIGINS:
        origins = [origin.strip() for origin in config.BACKEND_CORS_ORIGINS.split(",")]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET"],
            allow_headers=["*"],
        )

    app.add_middleware(GZipMiddleware, minimum_size=0)
    app.include_router(api_router, prefix=config.API_VERSION_STR)


@app.get("/ping", description="Health Check")
def ping():
    """Health check."""
    return {"ping": "pong!"}


if __name__ == '__main__':
    configure()
    uvicorn.run(app, port=8000, host='127.0.0.1')
else:
    configure()
