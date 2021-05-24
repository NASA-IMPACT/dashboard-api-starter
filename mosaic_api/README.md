# Mosaic API

An API to proxy STAC API searches into a MosaicJSON endpoint.

## Local Environment

First, add your AWS credentials to a new file called `.env`. You can see an example of this file at `.env.example`.

### Clone and configure

```bash
git clone https://github.com/MAAP-Project/dashboard-api-starter.git
cd dashboard-api-starter

# Add your AWS credentials to a new file called `.env`. You can see an example of this file at `.env.example`.
cp .env.example .env
# Copy and configure the app
cp mosaic_api/stack/config.yml.example mosaic_api/stack/config.yml
```

### Running the app locally

Install GDAL for your platform, possibly with directions from 
[TileMill](https://tilemill-project.github.io/tilemill/docs/guides/gdal/). 

On macOS, use the [KyngChaos](https://www.kyngchaos.com/software/frameworks/) 
installer, and put it on your path with:

```
echo 'export PATH=/Library/Frameworks/GDAL.framework/Programs:$PATH' >> ~/.bash_profile
source ~/.bash_profile
```

Create a Python environment and install the required dependencies.

    pyenv install 3.7.10
    pyenv init # and add to .bash_profile and source in current shell
    pyenv local 3.7.10
    pip install -e .
    pip install -e .[server]

Set the appropriate AWS_PROFILE if not default:

    export AWS_PROFILE=CHANGEME

If using a tiler other than `https://api.cogeo.xyz`, configure this as the `MOSAIC_API_ROOT` value in 
`mosaic_api/stack/config.yml`.

Run the app:

    python -m uvicorn mosaic_api.main:app --reload

Test the api:

```bash
curl -X "POST" "http://localhost:8000/v1/mosaics" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "stac_api_root": "https://earth-search.aws.element84.com/v0",
  "username": "your_username",
  "datetime": "2021-04-20T00:00:00Z/2021-04-21T02:00:00Z",
  "collections": [ "sentinel-s2-l2a-cogs" ],
  "bbox": [ 20, 20, 21, 21 ]
}'
```

### Running the app with docker:

```bash
docker-compose up --build
```

## Contribution & Development

Issues and pull requests are more than welcome.

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
