"""Test /v1/mosaics endpoints"""

import pytest
import json
from starlette import status


@pytest.fixture
def mock_mosaic_api_root(monkeypatch):
    monkeypatch.setenv("MOSAIC_API_ROOT", "http://example.com")


@pytest.fixture
def mock_execute_stac_search(mocker):
    mocker.patch(
        'mosaic_api.api.api_v1.endpoints.mosaics.execute_stac_search',
        return_value=[]
    )


def test_stac_api_no_results(app, mock_execute_stac_search):
    response = app.post(f"v1/mosaics",
                data=json.dumps({
                    "stac_api_root": "foo",
                    "username": "test_user"
                })
            )

    print(response.content)
    assert json.loads(response.content)["detail"] == 'Error: STAC API Search returned no results'
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_post_missing_parameters(app):
    response = app.post(f"v1/mosaics",
                data=json.dumps({
                    "stac_api_root": "",
                    "username": "test_user"
                })
            )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json.loads(response.content)["detail"] == 'Error: stac_api_root parameter must be defined.'

    response = app.post(f"v1/mosaics",
                data=json.dumps({
                    "stac_api_root": "https://earth-search.aws.element84.com/v0",
                    "username": ""
                })
            )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json.loads(response.content)["detail"] == 'Error: username parameter must be defined.'


def test_post_error_responses(app, mock_mosaic_api_root):
    response = app.post(f"v1/mosaics",
                data=json.dumps({
                    "stac_api_root": "https://earth-search.aws.element84.com/v0",
                    "username": "test_user"
                })
            )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert json.loads(response.content)["detail"] == \
           'Error: Error extracting mosaic data from results: Access Denied'



