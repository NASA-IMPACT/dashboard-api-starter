""" dashboard_api static datasets """
import json
import os
from typing import List

import botocore

from dashboard_api.core.config import (DATASET_METADATA_FILENAME,
                                   BUCKET,
                                   VECTOR_TILESERVER_URL,
                                   TITILER_SERVER_URL)
from dashboard_api.db.static.errors import InvalidIdentifier
from dashboard_api.db.static.sites import sites
from dashboard_api.db.utils import invoke_lambda, s3_get
from dashboard_api.models.static import DatasetInternal, Datasets, GeoJsonSource

data_dir = os.path.join(os.path.dirname(__file__))


class DatasetManager(object):
    """Default Dataset holder."""

    def __init__(self):
        """Load all datasets in a dict."""

        pass

    def _data(self):
        dataset_objects = self._load_metadata_from_file()
        return {
            key: DatasetInternal.parse_obj(dataset)
            for key, dataset in dataset_objects["_all"].items()
        }

    def _load_metadata_from_file(self):
        if os.environ.get('ENV') == 'local':
            # Useful for local testing
            example_datasets = "example-dataset-metadata.json"
            print(f'Loading {example_datasets}')
            return json.loads(open(example_datasets).read())
        try:
            s3_datasets = json.loads(
                s3_get(bucket=BUCKET, key=DATASET_METADATA_FILENAME)
            )
            print("datasets json successfully loaded from S3")
            return s3_datasets
        except botocore.errorfactory.ClientError as e:
            if e.response["Error"]["Code"] in ["ResourceNotFoundException", "NoSuchKey"]:
                return json.loads(open("example-dataset-metadata.json").read())
            else:
                raise e


    def get(self, spotlight_id: str, api_url: str) -> Datasets:
        """
        Fetches all the datasets available for a given spotlight. If the
        spotlight_id provided is "global" then this method will return
        all datasets that are NOT spotlight specific. Raises an
        `InvalidIdentifier` exception if the provided spotlight_id does
        not exist.

        Params:
        -------
        spotlight_id (str): spotlight id to return datasets for
        api_url(str): {scheme}://{host} of request originator in order
            to return correctly formated source urls

        Returns:
        -------
        (Datasets) pydantic model contains a list of datasets' metadata
        """

        global_datasets = self._process(
            self._load_metadata_from_file()["global"],
            api_url=api_url,
            spotlight_id="global",
        )

        if spotlight_id == "global":
            return Datasets(datasets=[dataset.dict() for dataset in global_datasets])

        # Verify that the requested spotlight exists
        site = sites.get(spotlight_id, api_url)
        if not site:
            raise InvalidIdentifier()

        spotlight_metadata = self._load_metadata_from_file().get(site.id)
        if spotlight_metadata:
            spotlight_datasets = self._process(
                spotlight_metadata, api_url=api_url, spotlight_id=site.id,
            )
        else:
            spotlight_datasets = []

        return Datasets(
            datasets=[
                dataset.dict() for dataset in [*global_datasets, *spotlight_datasets]
            ]
        )

    def get_all(self, api_url: str) -> Datasets:
        """Fetch all Datasets. Overload domain with S3 scanned domain"""
        datasets = self._process(
            datasets_domains_metadata=self._load_metadata_from_file()["_all"],
            api_url=api_url,
        )
        return Datasets(datasets=[dataset.dict() for dataset in datasets])

    def list(self) -> List[str]:
        """List all datasets"""
        return list(self._data().keys())

    def _format_urls(self, tiles: List[str], api_url: str, spotlight_id: str = None):
        if spotlight_id:
            [ tile.replace("{spotlightId}", spotlight_id) for tile in tiles ]
        return [
            tile.replace("{api_url}", api_url)
            .replace("{vector_tileserver_url}", VECTOR_TILESERVER_URL)
            .replace("{titiler_server_url}", TITILER_SERVER_URL)
            for tile in tiles
        ]

    def _process(
        self, datasets_domains_metadata: dict, api_url: str, spotlight_id: str = None
    ):
        """
        Processes datasets to be returned to the API consumer:
        - Updates dataset domains for all returned datasets
        - Inserts api url into source urls
        - Inserts spotlight id into source url (if a spotlight id is provided)

        Params:
        -------
        output_datasets (dict): Dataset domains for the datasets to be returned.
        api_url (str):
            Base url, of the form {schema}://{host}, extracted from the request, to
            prepend all tile source urls with.
        spotlight_id (Optional[str]):
            Spotlight ID (if requested), to be inserted into the source urls

        Returns:
        --------
        (list) : datasets metadata objects (to be serialized as a pydantic Datasets
            model)
        """
        output_datasets = {
            k: v
            for k, v in self._data().items()
            if k in datasets_domains_metadata.keys()
        }

        for k, dataset in output_datasets.items():

            # overload domain with domain returned from s3 file
            dataset.domain = datasets_domains_metadata[k].get("domain")

            # format url to contain the correct API host and
            # spotlight id (if a spotlight was requested)
            format_url_params = dict(api_url=api_url)
            if spotlight_id:
                if k == "nightlights-viirs" and spotlight_id in ["du", "gh"]:
                    spotlight_id = "EUPorts"
                format_url_params.update(dict(spotlight_id=spotlight_id))

            dataset.source.tiles = self._format_urls(
                tiles=dataset.source.tiles, **format_url_params
            )

            if dataset.source.source_url:
                dataset.source.source_url = dataset.source.source_url.replace("{vector_tileserver_url}", VECTOR_TILESERVER_URL)
                dataset.source.source_url = dataset.source.source_url.replace("{titiler_server_url}", TITILER_SERVER_URL)

            if dataset.background_source:
                dataset.background_source.tiles = self._format_urls(
                    tiles=dataset.background_source.tiles, **format_url_params
                )
            if dataset.compare:
                dataset.compare.source.tiles = self._format_urls(
                    tiles=dataset.compare.source.tiles, **format_url_params
                )
            # source URLs of background tiles for `detections-*` datasets are
            # handled differently in the front end so the the `source` objects
            # get updated here
            if k.startswith("detections-"):
                dataset.source = GeoJsonSource(
                    type=dataset.source.type, data=dataset.source.tiles[0]
                ).dict()

            if spotlight_id == "tk" and k == "water-chlorophyll":
                dataset.source.tiles = [
                    tile.replace("&rescale=-100%2C100", "")
                    for tile in dataset.source.tiles
                ]
        output_datasets = sorted(output_datasets.values(), key=lambda x: x.order)
        return output_datasets


datasets = DatasetManager()
