# Webtap

Webtap is a Python library designed to ...

# Requirements

Webtap has been developed and tested with Python 3.11
Make sure that your python version is >= 3.11

# Installing Webtap library

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

# Run examples

After installation you can run an example using the following command:
```bash
python -m examples.apify_tap_example
```
# Run tests
You can run tests by using the following command:
```bash
    python -m tests.apify_tap_test --apify_tap_id={actor_id} --model=gpt-3.5-turbo --test_num={test_num}
```
# Installing Webtap library from PyPI

To use Webtap in your project, you can install it directly from the Python Package Index (PyPI) using pip:

```bash
pip install webtap
```

Alternatively, if you are managing your project's dependencies through a `requirements.txt` file, you can add Webtap to it:
    
```bash
webtap
```

After adding the line to your `requirements.txt`, you can install all your dependencies with:
    
```bash
pip install -r requirements.txt
```

Add the following environment variables to your shell ( Add these to your .bashrc or .bash_profile to make them permanent):
```bash
export OPENAI_API_KEY="{your api key}"
export APIFY_API_TOKEN="{your api key}"
```

After that you can use the library in your project:
```python
from webtap.tap_manager import TapManager
from webtap.base_tap import BaseTap

tap_manager = TapManager()
tap = tap_manager.get_tap( "atg_epctex_gutenberg_scraper" ) # Project Gutenberg: a collection of 70,000 free ebooks
print(tap.get_retriever_and_run("Search for 'history', maximum 15 items, in Italian language, using Apify Proxy"))

```
# Creating a new Apify Tap using AI based Tap Generator

Webtap also offers a tool to automatically generate a new Apify Tap. 
It often works; when it doesn't work, it provides a good starting point for manual editing.
To do so, you can use the following python code:
(This feature is exclusive to the full GitHub repository and is not included in the PyPI package distribution.)

```bash
# make sure you Webtap project is setup(venv is activated, requirements are installed, environment variables are set and you are in the webtap directory)
python -m examples.tap_generator_example epctex/gutenberg-scraper
```
Check out the code in the `examples/tap_generator_example.py` file to see how to use the Tap Generator and how to customize the generated Tap.

# Creating a new standard Apify Tap using json definition

In order to see how to create a standard new ApifyTap (using json definition) see [GUIDE.md](docs/taps_definition/GUIDE.md)

# Creating a new Custom Apify Tap by extending the ApifyTap class

In order to see how to create a standard new ApifyTap (using json definition) see [CUSTOM_GUIDE.md](docs/taps_definition/CUSTOM_GUIDE.md)


## Ownership and Responsibility

This project was initially developed and is owned by **Webtap Technologies LLC**.

### Founding Contributors

- [stefanopochet Stefano](https://github.com/stefanopochet)
- [alpha8eta](https://github.com/alpha8eta)
- [klokt-valg H. H.](https://github.com/klokt-valg)

### Legal Disclaimer

All contributions to this project are made on a voluntary basis and do not imply any legal responsibility for individual contributors, including but not limited to founding contributors. Legal responsibility for this project and its use rests solely with Webtap Technologies LLC, as stated in the license.

### Contact Information

**Webtap Technologies LLC**  
30 N Gould ST STE R  
Sheridan, WY 82801  
EIN: 32-0763057Test PR from secondary account
