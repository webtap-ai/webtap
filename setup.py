from setuptools import setup, find_packages

setup(
    name="webtap",
    version="0.1.5",
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['*.json', '*.txt']},
    author="Stefano Pochet",
    author_email="stefanopochet@gmail.com",
    description="Accessing the Web's Deep Data Aquifers with a Simple Tap",
    url="https://github.com/webtap-ai/webtap.git", )
