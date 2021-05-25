"""Setup mosaic_api."""

from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "fastapi~=0.65.0",
    "pyyaml",
    "pystac-client~=0.1.1",
    "cogeo-mosaic~=3.0.0",
    "stac_pydantic", # inherit version from pystac-client
    "aiohttp~=3.7.4",
    "aiohttp[speedups]"
]
extra_reqs = {
    "dev": ["pytest", "pytest-cov", "pytest-asyncio", "pytest-mock", "pre-commit"],
    "server": ["uvicorn", "click==7.0"],
    "deploy": [
        "docker",
        "attrs",
        "aws-cdk.core>=1.72.0",
        "aws-cdk.aws_lambda>=1.72.0",
        "aws-cdk.aws_apigatewayv2>=1.72.0",
        "aws-cdk.aws_apigatewayv2_integrations>=1.72.0",
        "aws-cdk.aws_iam>=1.72.0",
    ],
    "test": ["moto[iam]", "mock", "pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="mosaic_api",
    version="0.1.0",
    description=u"",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="",
    author=u"Development Seed",
    author_email="info@developmentseed.org",
    url="https://github.com/developmentseed/dashboard_api",
    license="MIT",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    package_data={
        "mosaic_api": ["templates/*.html", "templates/*.xml", "db/static/**/*.json"]
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
