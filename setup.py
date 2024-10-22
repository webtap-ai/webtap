from setuptools import setup, find_packages

setup(
    name="webtap",
    version="0.4.5",
    packages=find_packages(),
    install_requires=[
        "aiohttp==3.8.3",
        "langchain==0.0.251",
        "openai==0.27.8",
        "tiktoken==0.4.0",
        "apify-client==1.5.0",    
        "demjson3==3.0.6",
        "black==24.4.2",
        "html2text==2024.2.26",
    ],
    include_package_data=True,
    package_data={"": ["*.json", "*.txt"]},
    author="Stefano Pochet",
    author_email="stefanopochet@gmail.com",
    description="Accessing the Web's Deep Data Aquifers with a Simple Tap",
    url="https://github.com/webtap-ai/webtap.git",
)
