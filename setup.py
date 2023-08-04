from setuptools import setup, find_packages

setup(
    name="webtap",
    version="0.1.1.4",
    packages=find_packages(),
    install_requires=[
        'langchain==0.0.251', 
        'openai==0.27.8',
        'tiktoken==0.4.0'
    ],
    include_package_data=True,
    package_data={'': ['*.json', '*.txt']},
    author="Stefano Pochet",
    author_email="stefanopochet@gmail.com",
    description="Accessing the Web's Deep Data Aquifers with a Simple Tap",
    url="https://github.com/webtap-ai/webtap.git", )
