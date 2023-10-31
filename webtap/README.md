# Tap generator for webtap

## Usage

```bash
python -m tap_generator.run {actor_id}
```

Example run

```bash
python -m tap_generator.run emastra/google-trends-scraper
```

## How the tap generator works

- The Tap generator will execute a series of 11 steps to generate a tap for a given actor.
- In tap_generator.py TapGenerator.generate_tap() you can check the order and the logic of the steps.
- Each step (except one) will generate one (or in one occsasion two) json files
- Each step requires that all the previous (non-optional) steps have been executed successfully. Which means the required json files have been generated and have the correct format/data.
- The Tap generator will create a folder in data/taps/atg\_{actor_id} with all files generated during the process.
- The tap generator will also create two log in logs/atg\_{actor_id}: a results.log which will contain a short summary of the process and a debug_trace.log which will contain a detailed log of the process.

## How to interact with the Tap generator and eventually fix issues

- If for some reason the tap generator is unable to fullfill a step, it will stop and communicate in the output the step that failed, a short description of the issue and **the name of the file that it hasn't been able to generate**.
- If you want to fix the issue and continue the process, you can do one of the following options:
  a. Read the debug_trace.log and try to fix the issue.
  b. **(Recommended)** Simply manually generaate the file that hasn't been generated and restart the process
