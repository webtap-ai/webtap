# Webtap

Webtap is a Python library designed to access any type of web data by using natural language.

# Example queries that can fulfilled by webtap

1. (Using Tripdvisor Tap) Hotels or vacation rentals in Paris, first week of September 2023, currency in EUR, language in Spanish, with email addresses
2. (Using Twitter Tap) Tweets from @ZelenskyyUa

# Requirements

Webtap has been developed and tested with Python 3.11

# Installing Webtap library

1. It is recommended, though not mandatory, to create a virtual environment for your project.
Virtual environments make it easier to manage packages and ensure that your project's dependencies are isolated from other Python projects.
2. Setup openai key: 
You must have an openai key set in your environment. You can setup one by adding the following in your ~/.zshrc file
```bash
export OPENAI_API_KEY="{your api key}"
```

3. Optionally you can setup:
Apify to run Apify actors (and get actual data)
```bash
export APIFY_API_TOKEN="{your api key}"
```
and LangSmith for LLM debugging by adding the following enviroment variables
```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="{Your dev environment project}"
export LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
export LANGCHAIN_API_KEY={your api_key}
```

3. pip install .

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

# Usage from third party project
Usage is pretty straihghtforward, init a tap, given a data_task (data you would like to get) ask for a "retriever" (a way to get that data through this tap) and than run it
Include the library in your pip requirements.txt (make sure that you git environment is correctly setup so that you can clone git private repos without typing password)
```bash
    webtap @ git+https://github.com/webtap-ai/webtap.git
```
After that include and use the library in the following way:
```python
    from webtap.tap_manager import TapManager
    # Load tap_manager
    tap_manager = TapManager()
    # get tap "tripadvisor"
    tap = tap_manager.get_tap("tripadvisor")
    # Get data for a specific data task
    sample_data_return = tap.retrieve_sample_data("Restaurants in Miami")
    logging.info("Apify tap sample data return: %s", sample_data_return)
    sample_data = sample_data_return["data"]

    # validate data
    validate_data_return = tap.validate_data(data_task, sample_data)
    logging.info("Apify tap validate data return: %s", validate_data_return)

```

# Creating a new Apify Tap by instantiating a new apify_tap object

In order to see how to create a standard new ApifyTap (using json definition) see [GUIDE.md](docs/taps_definition/GUIDE.md)

# Creating a new Apify Tap by extending the ApifyTap class

In order to see how to create a standard new ApifyTap (using json definition) see [CUSTOM_GUIDE.md](docs/taps_definition/CUSTOM_GUIDE.md)