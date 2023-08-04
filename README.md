# Webtap

Webtap is a Python library designed to access any type of web data by using natural language.

# Example queries that can fulfilled by webtap

1. List of restaurants in Paris, with email addresses and phone number
2. Hotels or vacation rentals in Paris, first week of September 2023, currency in EUR, language in Spanish, with email addresses

# Requirements

Webtap requires Python 3.9

# Installing Webtap library

Setting up a Virtual Environment (Optional)

1. It is recommended, though not mandatory, to create a virtual environment for your project. Virtual environments make it easier to manage packages and ensure that your project's dependencies are isolated from other Python projects.
2. Setup openai key
You must have an openai key set in your environment. You can add one in your ~/.zshrc file
```bash
export OPENAI_API_KEY="{your api key}"
```bash

3. Optionally you can setup Langsmith for LLM debugging by adding the following enviroment variables
```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="{Your dev environment project}"
export LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
export LANGCHAIN_API_KEY={your api_key}
```bash

3. pip install .

# Usage
Usage is pretty straihghtforward, init a tap, given a data_task (data you would like to get) ask for a "data model" (a way to get that data through this tap)
## Initialize a Tap
trip_advisor_tap = TripAdvisorTap()
## get a data model for given data_task
data_task = "Hotels or vacation rentals in Paris, first week of September 2023, currency in EUR, language in Spanish, with email addresses"
return = trip_advisor_tap.getDataModel(data_task) # return will be a dict containing the data model and few more info

# Run examples

After installation you can run examples using the following command:
python -m examples.apify_tap_example
python -m examples.tripadvisor_tap_example

# Creating a new Apify Tap by instantiating a new apify_tap object

You can create a new Apify Tap by simply defining information about how the Tap/Actor will work
See examples/apify_tap_example.py for an explanation about how to do so

# Creating a new Apify Tap by extending the ApifyTap class

You can create a new Apify Tap by extending an ApifyTap class and add the custom logic in it
See webtap/taps/tripadvisor/tripadvisor.py for an explanation about how to do so and examples/tripadvisor_tap_example.py about how to instantiate and use a custom object