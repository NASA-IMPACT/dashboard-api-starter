"""AWS Lambda handler for Mosaic."""

from mangum import Mangum

from mosaic_api.main import app

handler = Mangum(app, enable_lifespan=False)
