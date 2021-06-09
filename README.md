# dashboard-api-starter

A lightweight tile server for MAAP data, based on [titiler](https://github.com/developmentseed/titiler).

## Contributing data
More information for data contributors like expected input format and delivery mechanisms, can be found in the [data guidelines](guidelines/README.md).

## Local Environment

First, add your AWS credentials to a new file called `.env`. You can see an example of this file at `.env.example`.

### Clone and configure

```bash
git clone https://github.com/MAAP-Project/dashboard-api-starter.git
cd dashboard-api-starter
# Copy and configure the app
cp stack/config.yml.example stack/config.yml
```

Note, the local `stack/config.yml` file will only be used for running the app locally. Deployment is managed via github actions (See `.github/workflows/deploy.yml`).

Datasets for `/v1/datasets` are loaded from a json file stored in S3 unless `ENV=local` is set when running the app. The S3 location for these datasets is defined by the `BUCKET` and `DATASET_METADATA_FILENAME` values in `stack/config.yml`: `s3://{BUCKET}/{DATASET_METADATA_FILENAME}`.

### Running the app locally

To run the app locally, you can use `ENV=local` when running the app to use the `example-dataset-metadata.json` file as the source for `/v1/datasets`. This is useful for testing new dataset configurations.

**IMPORTANT:** Create if needed and ensure access to the buckets configured in `stack/config.yml`.

This requires read and write access to the s3 bucket in `stack/config.yml`.

```bash
pyenv install
pip install -e .
# Create or add buckets for your data files
export AWS_PROFILE=CHANGEME
# Run the app with dataset metadata stored on S3
uvicorn dashboard_api.main:app --reload
# Run the app with example-dataset-metadata.json - useful for testing
ENV=local uvicorn dashboard_api.main:app --reload
```

Test the api `open http://localhost:8000/v1/datasets`

### Running the app with docker:

```bash
docker-compose up --build
```

Test the api `open http://localhost:8000/v1/datasets`

## Contribution & Development

Issues and pull requests are more than welcome.

### If developing on the appplication, use pre-commit

This repo is set to use `pre-commit` to run *my-py*, *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when commiting new code.

```bash
$ pre-commit install
$ git add .
$ git commit -m'fix a really important thing'
black....................................................................Passed
Flake8...................................................................Passed
Verifying PEP257 Compliance..............................................Passed
mypy.....................................................................Passed
[precommit cc12c5a] fix a really important thing
 ```

in `stack/config.yml` and / or listing datasets from an external `STAC_API_URL`.

Metadata is used to list serve data via `/datasets`, `/tiles`, and `/timelapse` There are 2 possible sources of metadata for serving these resources.

1. Static JSON files, stored in `dashboard_api/db/static/datasets/`
2. STAC API, defined in `stack/config.yml`

In `lambda/dataset_metadata_generator` is code for a lambda to asynchronously generate metadata json files.

This lambda generates metadata in 2 ways:

1. Reads through the s3 bucket to generate a file that contains the datasets for each given spotlight option (_all, global, tk, ny, sf, la, be, du, gh) and their respective domain for each spotlight.
2. If `STAC_API_URL` is configured in `stack/config.yml`, fetches collections from a STAC catalogue and generates a metadata object for each collection.

## Cloud Deployment

Requirements:

* npm
* jq

### Install AWS CDK, pip requirements and run CDK bootstrap

`./install.sh` should only be run once and if requirements set in `setup.py` change.

```bash
export AWS_PROFILE=CHANGEME
# Install requirements: aws-cdk and pip
# Bootstrap the account
# Should only need to run this once unless pip requirements change.
./install.sh
```

Deploy the app!

This currently deploys 2 stacks.

```bash
export AWS_PROFILE=CHANGEME
# Note - the docker build is currently slow so this can take 5+ minutes to run 
./deploy.sh
```

Deploy the dashboard!

```bash
# Suggest changing your parent directory for distinct repository organization
cd ..
git clone git@github.com:MAAP-Project/earthdata-dashboard-starter.git
cd earthdata-dashboard-starter
nvm install
# configure the API_URL to be the same (you might need to add `v1/` at the end) as returned from `./deploy.sh`
API_URL=<REPLACE_ME> yarn deploy
```
