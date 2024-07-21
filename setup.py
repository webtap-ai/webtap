from setuptools import setup, find_packages


""" This doesn't work currently
import yaml
# Load version from config.yml
with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
    version = config["library"]["version"]
"""

setup(
    name="webtap",
    version="0.3.65",
    packages=find_packages(),
    install_requires=[
        "aiohttp==3.9.4",
        "langchain==0.0.251",
        "openai==0.27.8",
        "tiktoken==0.4.0",
        "apify-client==1.5.0",
        "demjson3",
        "black",
        "html2text",
    ],
    include_package_data=True,
    package_data={"": ["*.json", "*.txt"]},
    author="Stefano Pochet",
    author_email="stefanopochet@gmail.com",
    description="Accessing the Web's Deep Data Aquifers with a Simple Tap",
    url="https://github.com/webtap-ai/webtap.git",
)
