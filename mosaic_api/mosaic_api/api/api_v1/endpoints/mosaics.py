"""Mosaic endpoints."""
from mosaic_api.models.mosaics import Mosaic, MosaicRequest, Link
import random
import string
from fastapi import APIRouter, Response, HTTPException
from starlette import status
from starlette.requests import Request
from cogeo_mosaic.mosaic import MosaicJSON
from rio_tiler.io import COGReader
from pystac_client import Client
from typing import List, Optional
from asyncio import wait_for, create_task
import asyncio
import aiohttp

from mosaic_api.core.config import MOSAIC_API_ROOT

router = APIRouter()


@router.get(
    "/mosaics/{mosaic_id}",
    responses={
        200: {"description": "return mosaic for a given ID"}
    },
    response_model=Mosaic,
)
async def get_mosaic(
        mosaic_id: str
) -> Mosaic:
    """Return mosaic info for the given mosaic ID"""
    # todo: should this check if the mosaic actually exists, or just return the tilejson url?
    if mosaic_id:
        return _mosaic(mosaic_id)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid mosaic ID")


@router.post(
    "/mosaics",
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "Create a new mosaic"}},
    response_model=Mosaic,
)
async def post_mosaics(
        request: Request,
        response: Response,
        mosaic_request: MosaicRequest) -> Mosaic:
    """Create a mosaic for the given parameters"""

    if not mosaic_request.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Error: username parameter must be defined.")

    if not mosaic_request.stac_api_root:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Error: stac_api_root parameter must be defined.")

    # titiler requires layername to be <=32 chars
    layername = ''.join(random.choice(string.ascii_letters) for _ in range(32))

    loop = asyncio.get_running_loop()

    try:
        try:
            features = await wait_for(loop.run_in_executor(None, execute_stac_search, mosaic_request), 10)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error: timeout executing STAC API search")

        if not features:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error: STAC API Search returned no results")

        try:
            # 20 seconds should be enough to read the info from a COG, but may take longer on a non-COG
            mosaic_data = await wait_for(loop.run_in_executor(None, extract_mosaic_data, features), 20)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error: timeout reading a COG asset and generating MosaicJSON definition")

        if mosaic_data is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error: could not extract mosaic data")

        try:
            token = await wait_for(retrieve_token(mosaic_request.username), 5)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error: timeout getting mosaicer access token")

        try:
            mosaic_id = await wait_for(create_mosaic_remote(layername, mosaic_request.username, token, mosaic_data), 5)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error: timeout creating mosaic in mosaicer service")

        response.headers["Location"] = f"{request.url.scheme}://{request.headers['host']}/v1/mosaics/{mosaic_id}"

        return _mosaic(mosaic_id)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {e}")


async def create_mosaic_remote(layername: str, username: str, token: str, mosaic_data) -> str:
    mosaic_api_uri = f"{MOSAIC_API_ROOT}/mosaicjson/upload"
    req_body = {
        "username": username,
        "layername": layername,
        "mosaic": mosaic_data.dict(exclude_none=True),
        "overwrite": True
    }
    req_params = {
        "access_token": token,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(mosaic_api_uri, json=req_body, params=req_params) as r:
                if r.status == status.HTTP_200_OK:
                    return (await r.json())['mosaic']
                else:
                    raise Exception(f"Non-200 creating mosaic layer: {r.status} {(await r.text())[:1024]}")
    except Exception as e:
        raise Exception(f"Error creating mosaic on {mosaic_api_uri}: {e}")


# assumes all assets are uniform. get the min and max zoom from the first.
def extract_mosaic_data(features: List[dict]) -> Optional[MosaicJSON]:
    if features:
        try:
            with COGReader(visual_asset_href(features[0])) as cog:
                info = cog.info()
            return MosaicJSON.from_features(
                features,
                minzoom=info.minzoom,
                maxzoom=info.maxzoom,
                accessor=visual_asset_href
            )
        except Exception as e:
            raise Exception(f"Error extracting mosaic data from results: {e}")
    else:
        return None


async def retrieve_token(username: str) -> str:
    token_uri = f"{MOSAIC_API_ROOT}/tokens/create"
    req_body = {
        "username": username,
        "scope": ["mosaic:read", "mosaic:create"]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(token_uri, json=req_body) as r:
                if r.status == status.HTTP_200_OK:
                    return (await r.json())['token']
                else:
                    raise Exception(f"Non-200 retrieving token : {r.status} {(await r.text())[:1024]}")
    except Exception as e:
        raise Exception(f"Error retrieving token from {token_uri}: {e}")


def execute_stac_search(mosaic_request: MosaicRequest) -> List[dict]:
    try:
        return Client.open(mosaic_request.stac_api_root).search(
            ids=mosaic_request.ids,
            collections=mosaic_request.collections,
            datetime=mosaic_request.datetime,
            bbox=mosaic_request.bbox,
            intersects=mosaic_request.intersects,
            query=mosaic_request.query,
            max_items=1000,  # todo: should this be a parameter? should an error be returned if more than 1000 in query?
            limit=500
            # setting limit to a higher value causes an error https://github.com/stac-utils/pystac-client/issues/56
        ).items_as_collection().to_dict()['features']
    except Exception as e:
        raise Exception(f"STAC Search error: {e}")


def _mosaic(mosaic_id: str) -> Mosaic:
    return Mosaic(
        id=mosaic_id,
        links=[
            Link(
                href=f"{MOSAIC_API_ROOT}/mosaicjson/{mosaic_id}/tilejson.json",
                rel="tilejson",
                type="application/json",
                title="TileJSON"
            )
        ]
    )


# todo: make this safer in case visual doesn't exist
def visual_asset_href(feature: dict) -> str:
    return feature['assets']['visual']['href']
