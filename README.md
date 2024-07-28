<div align="center" style="display: flex; align-items: center;">
  <a href="https://webtap.ai?utm_source=github" target="_blank">
    <picture>
      <source srcset="https://webtap.ai/images/webtap-logo-text-transparent-bg-with-shadow.png" media="(prefers-color-scheme: light)">
      <img alt="Webtap Logo" src="https://webtap.ai/images/webtap-logo-text-nobg.png" width="280" style="height: auto;">
    </picture>
  </a>
</div>

<p align="center">
  <a href="https://pypi.org/project/webtap/">
    <img src="https://img.shields.io/pypi/v/webtap" alt="PIP Version">
  </a>
  <a href="https://github.com/webtap-ai/webtap/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/webtap-ai/webtap" alt="MIT License">
  </a>
  <a href="https://github.com/webtap-ai/webtap/pulls">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="Send PR">
  </a>
</p>

<h1 align="center">
  Try the beta for free on webtap.ai
</h1>

<p align="center">
  <br />
  <a href="https://webtap.ai" rel="dofollow">Test drive ready-to-go beta app</a>
<br />


# Webtap: A Novel Approach to AI-Based Web Scraping 🌐

Webtap is a Python library that enables reliable, AI-driven web scraping. It leverages Large Language Models (LLMs) to orchestrate established scraping libraries, such as Apify, for efficient data extraction from the web.

#### The Problem 🚧

Modern websites use measures like captchas and IP blocking to hinder automated data extraction. With frequent changes in their layout and content, these defenses can challenge AI-based scrapers, resulting in less reliable data collection.

#### The Solution ✅

Webtap combines Apify's specialized scraping libraries with Large Language Models (LLMs) for smart web navigation and dynamic content adaptation, streamlining data extraction.

#### Python example use case 🐍

The code below shows how to use Webtap to find up to 15 'history'-themed books in Italian using Apify Proxy.
```python

  tap_manager = TapManager()
  tap = tap_manager.get_tap( "atg_epctex_gutenberg_scraper" ) # Project Gutenberg: a collection of 70,000 free ebooks
  print(tap.get_retriever_and_run("Search for 'history', maximum 15 items, in Italian language, using Apify Proxy"))

  # The above print statement will output real time scraped data from project gutenberg in the following format:
  # {
  #   'retriever_result': ApifyRetrieverResult(can_fulfill=True, explanation='...', retriever=...),
  #   'data': '[{"author": "Albertazzi, Adolfo, 1865-1924", "title": "Novelle umoristiche by Adolfo Albertazzi", ...}]'
  # }

```
# Try it now on webtap.ai 🚀

Experience Webtap's beta version directly on [webtap.ai](https://webtap.ai?utm_source=github) with no installation needed—simply sign up to begin scraping for free.

[**🚀 Get Started**](https://webtap.ai/signup)

# Empower your Apify Actors with AI 🤖

If you have built (or are planning to build) an Apify actor and want to enhance its capabilities with AI, Webtap is the perfect tool for you. By integrating Webtap into your actor, you can make it possible to access your actor's data using AI-based natural language queries. Follow instructions to [create a new Apify Tap](#creating-a-new-apify-tap) to learn how to do this.

# Python Library Installation 🐍

## Requirements

Webtap has been developed and tested with Python 3.11
Make sure that your python version is >= 3.11

## Installing Webtap library

1. Clone the repo
```bash 
git clone https://github.com/webtap-ai/webtap.git
cd webtap
```
2. It is recommended, though not mandatory, to create a virtual environment for your project.
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Setup openai key and Apify Key
You must have an openai key and a Apify key in order to use the project. You can get an openai key by signing up at https://platform.openai.com/ and an Apify key by signing up at https://apify.com/
Set the following environment variables in your shell ( Add these to your .bashrc or .bash_profile to make them permanent):
```bash
export OPENAI_API_KEY="{your api key}"
export APIFY_API_TOKEN="{your api key}"
```
Optionally setup LangSmith (signup at https://langsmith.com) environment variables if you want to use LangSmith for tracing:
```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="{Your dev environment project}"
export LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
export LANGCHAIN_API_KEY={your api_key}
```
4. Install requirements
```bash
python setup.py install
```

## Run examples

After installation you can run an example using the following command:
```bash
python -m examples.apify_tap_example
```

## Alternativelly you can install the library using pip

To use Webtap in your project, you can install it directly from the Python Package Index (PyPI) using pip:

```bash
pip install webtap
```

After installing the library, follow the steps to set up the environment variables and run the examples as described in "Setup openai key and Apify Key section (2), (3) and (4)".

## Managing dependencies with requirements.txt

If you are managing your project's dependencies through a `requirements.txt` file, you can add Webtap to it:
    
```bash
webtap
```

After adding the line to your `requirements.txt`, you can install all your dependencies with:
    
```bash
pip install -r requirements.txt
```

# Creating a new Apify Tap 🚰

Webtap supports out of the box a selection of the top 40 Apify actors, enabling immediate use. You can also define your own Tap following one of the three methods below:

## 1. Create a new Apify Tap automatically using the Tap Generator

The Tap Generator is a tool that automatically generates a new Apify Tap based on a JSON definition.
It often works; when it doesn't work, it provides a good starting point for manual editing.
To do so, you can use the following python code:
(This feature is exclusive to the full GitHub repository and is not included in the PyPI package distribution.)

```bash
# make sure you Webtap project is setup(venv is activated, requirements are installed, environment variables are set and you are in the webtap directory)
python -m examples.tap_generator_example epctex/gutenberg-scraper
```
Check out the code in the `examples/tap_generator_example.py` file to see how to use the Tap Generator and how to customize the generated Tap.

## 2. Creating a new standard Apify Tap using json definition

In order to see how to create a standard new ApifyTap (using json definition) see [GUIDE.md](docs/taps_definition/GUIDE.md)

## 3. Creating a new Custom Apify Tap by extending the ApifyTap class

In order to see how to create a standard new ApifyTap (using json definition) see [CUSTOM_GUIDE.md](docs/taps_definition/CUSTOM_GUIDE.md)

## Current State and Limitations 🚦

The Webtap Python library is currently tailored to work with Apify. It readily supports a selection of the top 40 Apify actors, enabling immediate use. Additionally, the Universal Scraper is on offer as a versatile LLM-based tool capable of scraping any website, albeit with varying efficiency compared to a bespoke Apify actor.

### Main use cases:

- Utilize any of the 40 immediately available Apify actors for website data scraping.
- Employ the Universal Scraper for a generic LLM-based approach to scrape any website.
- Access your custom Apify actors using intuitive natural language queries.
- Craft a tap tailored to your specific scraping requirements with the Tap Generator, or do it manually for more control.

## Roadmap 🗺️

- Integration with the full suite of public Apify actors, totaling over 1500, is under consideration for future updates.
- We are exploring the possibility of broadening our scraping toolset to include additional libraries such as Scrapy.
- Enhancements to the Universal Scraper are continuously evaluated, aiming to enhance its efficiency and dependability.

# Acknowledgments

This project would not have been possible without the following open-source libraries and services:


- [Apify SDK](https://sdk.apify.com/) for web crawling and automation.
- [LangChain](https://github.com/langchain-ai/langchain) for integrating language models into applications.
- [OpenAI](https://openai.com/) for providing access to powerful AI models.
- [LangSmith](https://smith.langchain.com/) for their tracing and debugging tools.
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation and settings management using Python type annotations.
- [tiktoken](https://pypi.org/project/tiktoken/) for handling TikTok tokens.
- [apify-client](https://pypi.org/project/apify-client/) for interacting with the Apify API.
- [demjson](https://pypi.org/project/demjson3/) for encoding, decoding, and linting JSON.
- [black](https://black.readthedocs.io/en/stable/) for formatting Python code.
- [html2text](https://pypi.org/project/html2text/) for converting HTML into clean, easy-to-read plain ASCII text.

We are grateful to the developers of these libraries and services for their hard work and dedication!

## Ownership and Responsibility

This project was initially developed and is owned by **Webtap Technologies LLC**.

### Founding Contributors

- [stefanopochet Stefano](https://github.com/stefanopochet)
- [alpha8eta](https://github.com/alpha8eta)
- [klokt-valg H. H.](https://github.com/klokt-valg)

### Legal Disclaimer

All contributions to this project are made on a voluntary basis and do not imply any legal responsibility for individual contributors, including but not limited to founding contributors. Legal responsibility for this project and its use rests solpely with Webtap Technologies LLC, as stated in the license.

### Contact Information

**Webtap Technologies LLC**  
30 N Gould ST STE R  
Sheridan, WY 82801  
EIN: 32-0763057