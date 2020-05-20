""" covid_api static sites """
import os
from typing import List

from covid_api.models.static import Site, Sites
from covid_api.db.static.errors import InvalidIdentifier
data_dir = os.path.join(os.path.dirname(__file__))

class SiteManager(object):
    """Default Site holder."""

    def __init__(self):
        """Load all datasets in a dict."""
        sites = [
            os.path.splitext(f)[0] for f in os.listdir(data_dir) if f.endswith(".json")
        ]

        self._data = {
            site: Site.parse_file(os.path.join(data_dir, f"{site}.json"))
            for site in sites
        }

    def get(self, identifier: str) -> Site:
        """Fetch a Site."""
        try:
            return self._data[identifier]
        except KeyError:
            raise InvalidIdentifier(f"Invalid identifier: {identifier}")

    def get_all(self) -> Sites:
        """Fetch all Sites."""
        return Sites(
            sites=[site.dict() for site in self._data.values()]
        )

    def list(self) -> List[str]:
        """List all sites"""
        return list(self._data.keys())

sites = SiteManager()