"""Test /v1/mosaics endpoints"""

import pytest
import json
from starlette import status


@pytest.mark.integ
def test_get_mosaic(app):
    mosaic_id = "foo"
    response = app.get(f"v1/mosaics/{mosaic_id}")

    assert response.status_code == status.HTTP_200_OK
    content = json.loads(response.content)

    assert content["id"] == mosaic_id
    link_tilejson = next(filter(lambda x: x["rel"] == "tilejson", content["links"]))
    assert link_tilejson["href"] == f"https://api.cogeo.xyz/mosaicjson/{mosaic_id}/tilejson.json"


@pytest.mark.integ
def test_post_mosaics(app):
    response = app.post(f"v1/mosaics",
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                },
                data=json.dumps({
                    "stac_api_root": "https://earth-search.aws.element84.com/v0",
                    "username": "test_user",
                    "datetime": "2021-04-20T00:00:00Z/2021-04-21T02:00:00Z",
                    "collections": [
                        "sentinel-s2-l2a-cogs"
                    ],
                    "bbox": [
                        20,
                        20,
                        21,
                        21
                    ]
                })
            )

    assert response.status_code == status.HTTP_201_CREATED
    content = json.loads(response.content)

    mosaic_id = content["id"]
    assert mosaic_id.startswith("test_user")
    link_tilejson = next(filter(lambda x: x["rel"] == "tilejson", content["links"]))
    assert link_tilejson["href"] == f"https://api.cogeo.xyz/mosaicjson/{mosaic_id}/tilejson.json"

    assert response.headers["Location"] == f"http://testserver/v1/mosaics/{mosaic_id}"
