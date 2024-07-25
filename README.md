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

# Usage from third party project
Usage is pretty straihghtforward: get a tap from Tap Manager, given a data_task (data you would like to get) retriever sample data (a way to get that data through this tap.

Include the library in your pip requirements.txt (make sure that you git environment is correctly setup so that you can clone git private repos without typing password):
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
EIN: 32-0763057