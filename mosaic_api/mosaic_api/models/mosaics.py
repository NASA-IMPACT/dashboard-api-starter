"""Static models."""

from typing import List, Optional

from stac_pydantic.api import Search
from pydantic import BaseModel


def to_camel(snake_str: str) -> str:
    """
    Converts snake_case_string to camelCaseString
    """
    first, *others = snake_str.split("_")
    return "".join([first.lower(), *map(str.title, others)])


# Link and Links derived from models in https://github.com/stac-utils/stac-pydantic
class Link(BaseModel):
    """Link Relation"""

    href: str
    rel: str
    type: Optional[str]
    title: Optional[str]


class Mosaic(BaseModel):
    """Dataset Model."""

    id: str # titiler mosaic value
    links: List[Link]

    class Config:
        """Generates alias to convert all fieldnames from snake_case to camelCase"""

        alias_generator = to_camel
        allow_population_by_field_name = True


class Mosaics(BaseModel):
    """Mosaic List Model."""

    mosaics: List[Mosaic]


class MosaicRequest(Search):
    """Mosaic request model."""

    stac_api_root: str
    username: str
    collections: Optional[List[str]] = None


#     {'username': 'philvarner', 'layername': 's2-l2a-cogs_20210520_53', 'mosaic': 'philvarner.s2-l2a-cogs_20210520_53'}
class TitilerMosaicResponse(BaseModel):
    """Titiler mosaicjson creation response model."""
    username: str
    layername: str
    mosaic: str