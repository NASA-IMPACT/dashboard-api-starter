"""Mosaic endpoints."""
from mosaic_api.models.mosaics import Mosaic, MosaicRequest, Link
import random
import string
from fastapi import APIRouter, Response, HTTPException
from starlette import status
from starlette.requests import Request
import requests
from cogeo_mosaic.mosaic import MosaicJSON
from rio_tiler.io import COGReader
from pystac_client import Client
from typing import List, Optional
from asyncio import wait_for, create_task
import asyncio

from mosaic_api.core.config import MOSAIC_API_ROOT

router = APIRouter()


@router.get(
    "/mosaics/{mosaic_id}",
    responses={
        200: { "description":"return mosaic for a given ID"}
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error: username parameter must be defined.")

    if not mosaic_request.stac_api_root:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error: stac_api_root parameter must be defined.")

    # titiler requires layername to be <=32 chars
    layername = ''.join(random.choice(string.ascii_letters) for _ in range(32))

    try:
        task_token = create_task(retrieve_token(mosaic_request.username))

        features = await wait_for(execute_stac_search(mosaic_request), 10)

        mosaic_data = await wait_for(extract_mosaic_data(features), 20)

        token = await wait_for(task_token, 5)

        mosaic_id = await wait_for(create_mosaic_remote(layername, mosaic_request.username, token, mosaic_data), 5)

        response.headers["Location"] = f"{request.url.scheme}://{request.headers['host']}/v1/mosaics/{mosaic_id}"

        return _mosaic(mosaic_id)
    except asyncio.TimeoutError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: timeout: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {e}")


async def create_mosaic_remote(layername: str, username: str, token: str, mosaic_data) -> requests.Response:
    mosaic_api_uri = f"{MOSAIC_API_ROOT}/mosaicjson/upload"
    try:
        r = requests.post(
            mosaic_api_uri,
            json={
                "username": username,
                "layername": layername,
                "mosaic": mosaic_data.dict(exclude_none=True),
                "overwrite": True
            },
            params={
                "access_token": token,
            }
        )
        if r.status_code == status.HTTP_200_OK:
            return r.json()['mosaic']
        else:
            raise Exception(f"Non-200 creating mosaic layer: {r.status_code} {r.text}")
    except Exception as e:
        raise Exception(f"Error creating mosaic on {mosaic_api_uri}: {e}")


# assumes all assets are uniform. get the min and max zoom from the first.
async def extract_mosaic_data(features: List[dict]) -> Optional[MosaicJSON]:
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
    try:
        r = requests.post(
            token_uri,
            json={
                "username": username,
                "scope": ["mosaic:read", "mosaic:create"]
            }
        )
        if r.status_code == status.HTTP_200_OK:
            return r.json()["token"]
        else:
            raise Exception(f"Non-200 retrieiving token: {r.status_code}")
    except Exception as e:
        raise Exception(f"Error retrieving token from {token_uri}: {e}")


async def execute_stac_search(mosaic_request: MosaicRequest) -> List[dict]:
    try:
        return Client.open(mosaic_request.stac_api_root).search(
            ids=mosaic_request.ids,
            collections=mosaic_request.collections,
            datetime=mosaic_request.datetime,
            bbox=mosaic_request.bbox,
            intersects=mosaic_request.intersects,
            query=mosaic_request.query,
            max_items=1000, # todo: should this be a parameter? should an error be returned if more than 1000 in query?
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
