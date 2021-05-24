"""Config."""

import os

import yaml

config_object = yaml.load(
    open(f"{os.path.abspath('')}/stack/config.yml", "r"), Loader=yaml.FullLoader
)

STAGE = os.environ.get("STAGE", config_object["STAGE"])
API_VERSION_STR = "/v1"

PROJECT_NAME = config_object["PROJECT_NAME"]

SERVER_NAME = os.getenv("SERVER_NAME")
SERVER_HOST = os.getenv("SERVER_HOST")
BACKEND_CORS_ORIGINS = os.getenv(
    "BACKEND_CORS_ORIGINS", default="*"
)  # a string of origins separated by commas, e.g: "http://localhost, http://localhost:4200, http://localhost:3000, http://localhost:8080, http://local.dockertoolbox.tiangolo.com"

DT_FORMAT = "%Y-%m-%d"

MOSAIC_API_ROOT = os.environ.get("MOSAIC_API_ROOT", config_object["MOSAIC_API_ROOT"])
