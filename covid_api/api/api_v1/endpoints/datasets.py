"""Dataset endpoints."""

from fastapi import APIRouter

from covid_api.models.static import Datasets
from covid_api.db.static.datasets import datasets


router = APIRouter()


@router.get(
    "/datasets",
    responses={200: dict(description="return a list of all available datasets")},
    response_model=Datasets,
)
def get_datasets():
    """Return a list of datasets."""
    return datasets.get_all()


@router.get(
    "/datasets/{spotlight_id}",
    responses={
        200: dict(description="return datasets available for a given spotlight")
    },
    response_model=Datasets,
)
def get_dataset(spotlight_id: str):
    """Return dataset info."""
    return datasets.get(spotlight_id)
