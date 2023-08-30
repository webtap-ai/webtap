# Guide to the define new Apify Taps

This document outlines the process to define new Apify Taps. You can enable GitHub Copilot to assist you while writing.
The following guide is about defining Standard Apify Taps, using just a json definition.
Alternatively it's possible to define a new Apify Tap by extending the ApifyTap class and adding the custom logic in it. See [Creating a new Apify Tap by extending the ApifyTap class](#creating-a-new-apify-tap-by-extending-the-apifytap-class) for more information.

## Steps

1. **Create Directory and Files**: In `data/taps`, create a new directory `{newactor_dir}` (you can choose any name you like) and copy all files from the `data/taps/tripadvisor` directory.

2. **Update Tap Manager**: In `data/tap_manager/tap_index.json`, create a JSON item `{ newactor_id : { config_dir : { {newactor_dir} } }`. `{newactor_id}` will be the tap id served by the API; you can choose any name you like.

3. **Edit tap_description.json Manually**:
   - Entities, filters, and options are a way to define a draft of a universal "Data retriever model". They are not used now but might be used in future engineering improvements.
   - This is the definition of a tap, not an actor. The filters/options are about the ways the end user can request data through the Tap. For example, ApifyProxy shouldn't be presented as an option.
   - For now, set special instructions as empty - maybe add "Always set proxyConfiguration : {  \"useApifyProxy\": true    }".

4. **Edit actor-description.json Manually**:
   - Id is the original Apify Actor Id (you can find it in the API endpoints of the actor view in the Apify console).
   - Name and description are the original Apify Actor Name and Description.

5. **Define Actor Input Schema**:
   - Copy the actor original input description and input JSON example into `docs/taps_definition/prompts/define-input-schema-prompt.txt`.
   - Run the prompt in chatgpt 4 code interpreter.
   - Review the prompt returned.
   - Paste the JSON part inside into `actor-input-json-schema.json`.

6. **Define Actor Input Summary**:
   - In the same chat window used above write: "Now report me a comma-separated list of all the JSON items. Return me a string."
   - Review the prompt returned.
   - Copy the result into `actor-input-summary.json`.

7. **Define Actor Output Fields**:
   - Get the text of an example output (Run once the actor or in the Actor description you may find an example output).
   - Copy that into `docs/taps_definition/prompts/define-output-fields-prompt.txt`.
   - Run the prompt in chatgpt 4 code interpreter.
   - Review the prompt returned.
   - Paste it inside into `actor-output-fields.json`.

8. **Prepare Examples/Tests**: Set `tap-example.json` and `tests-cases` as an empty List (`[]`).

9. **Define Test-Cases and Examples**:
   - It is best to define tests/example that will cover all entities, filters, and options. Depending on the complexity you usually need to define between 3 and 20 tests.
   - The test run will check that all the fields defined in the test case will exactly match the fields returned by the actor (the ones not defined will simply be ignored and the test will pass).
   - For the above reason: the fields explanation, alternative_fulfillable_data_task, outputCompatibility, and inputCompatibility have to be not present in tests-cases.
   - The test will also run an actual Apify call (and check that data is returned).
   - The test is considered valid if (1) data returned by the prompt respects the test case definition and (2) the actual Apify call returns data.
   - The test will also run a new prompt to check output returned by Apify validity. This last check is only to help reading tests, at this point whatever the prompt says the test will still pass.
   - You can omit "input_params": if you don't define input_params the test will simply not check the validity of input params (and not run any Apify call).
   - For the first test run it is useful to not define any input params, for the final test definition you should define as well input_params.

   For each test:
   a. Manually define a base test-case like the following example:
      ```json
      {
          "data_task": "Tweets from https://twitter.com/ZelenskyyUa",
          "expected_output": {
              "can_fulfill": true
          }
      }
      ```
    b. Run the test (source `venv/bin/activate` if you are not in the virtual env):
      ```bash
      python -m tests.apify_tap_test --apify_tap_id={newactor_id} --model=gpt-3.5-turbo --test_num={test_num}
      ```
      (example: `python -m tests.apify_tap_test --apify_tap_id=tripadvisor --model=gpt-3.5-turbo --test_num=0`)`
   c. Check the logs `logs/{newactor_id}/{today_datetime}/{test_num}.log`. If it has failed (see the log last line):
      - Have a look at the LangSmith output log; specifically check the prompt text returned before and after the JSON.
      - Usually, you can "fix" it by adding the "solution" as special instructions and/or as an example.
      If it says passed, still manually check the test log output (specifically the data returned) to check that it is actually valid and move to (9.d).
   d. Paste examples and tests data:
      - For examples:
        - Create a new JSON item with two properties `data_task` and `final_json_response`; manually set `data_task` to your given data_task.
        - Open LangSmith, copy the JSON returned by the prompt it into the given `examples.json` `final_json_response`.
        - Review and eventually edit the explanation and `alternative_fulfillable_data_task`.
      - For test-cases:
        - If test is `can_fulfill` true:
          - Add property `alternative_fulfillable_data_task` to null.
          - Add property `retriever` (take one from another test case - if it's the first take from another tap's test case).
          - Manually set `retriever` id and `actorId`.
          - Set `body` from the `input_params` of the LangSmith JSON returned.
        - If test is `can_fulfill` false no more work is needed.
   e. Rerun the test case.

10. **Final Test**: Once all tests/examples are defined run a final test:
    ```bash
    python -m tests.apify_tap_test --apify_tap_id={newactor_id} --model=gpt-3.5-turbo
    ```