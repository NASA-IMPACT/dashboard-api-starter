"""mosaic_api api."""

from mosaic_api.api.api_v1.endpoints import mosaics

from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(mosaics.router, tags=["mosaics"])
