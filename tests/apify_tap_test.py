import json, sys
import unittest
import logging
import os
from importlib.resources import files
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from webtap.tap_manager import TapManager
import argparse

'''
    This is a full test (run 10 tests in parallel) for any apify tap (the given tap_id will be defined by the apify_tap_id argument).
'''

class TestWebtap(unittest.TestCase):

    current_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger_main_dir = None

    def setUp(self):
        self.results = {}
        self.loggers = []

    def check_atomic_values(self, result, expected_output, logger):
        '''
        This function checks if the atomic values of the result correspond to the expected_output.
        '''
        all_passed = True
        for field, value in result.items():
            expected_value = expected_output.get(field)
            if expected_value is None:
                logger.info(f"Condition PASSED - The field {field} is not present in the expected result.")
            elif isinstance(value, dict):
                all_dict_passed = self.check_atomic_values(value, expected_value, logger)
                if not all_dict_passed:
                    all_passed = False
            else:
                if value != expected_value:
                    logger.warning(f"Condition NOT PASSED - The field {field} (data {value}) doesn't correspond to the expected result ({expected_value}).")
                    all_passed = False
                else:
                    logger.info(f"Condition PASSED - The field {field} (data {value}) corresponds to the expected result ({expected_value}).")
        return all_passed

    def run_test(self, i, test_case):
        '''
        This function runs a single test case
        '''
        # Create a logger for each test_case / thread
        log_filename = f'{i}.log'
        logger = logging.getLogger(f'test_{i}')
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.logger_main_dir.joinpath(log_filename))
        logger.addHandler(fh)
        self.loggers.append(logger)

        logger.info(f'Running test {i}...')
        logger.info(f'Input: {test_case["data_task"]}')

        tap = TapManager().get_tap( os.environ["TESTRUN_APIFY_TAP_ID"] )
        # Set the logger of the tap to the main logger
        tap._logger = logger
        # set the model to the one defined in the env variable
        tap.set_llm_model(os.environ["TESTRUN_MODEL"])
        tap._logger.info(f"Model has been set to: {tap.openai_model}")

        tap._logger.info(f"***** Step 1. Testing retriever *****")

        retriever_result = tap.get_retriever(test_case['data_task'])
        logger.info(f'Retriever result: {retriever_result}')

        if retriever_result.can_fulfill is False:
            # if can_fulfill
            if test_case['expected_output']["can_fulfill"] is False:
                
                # generate example template
                example_template = {
                    "data_task": test_case['data_task'],
                    "final_json_response": {
                        "inputCompatibility": f"Only using the params provided {tap.name} INPUT SCHEMA: No, I am not 100% sure that I can fulfill the params required by given task",
                        "outputCompatibility": f"Assuming data returned by {tap.name} is reliable and solely based on compatibility between DATA TASK and {tap.name} OUTPUT RETURN FIELDS: No, I am not 100% sure that I can fulfill the given task given {tap.name} OUTPUT RETURN FIELDS",
                        "can_fulfill": False,
                        "explanation": f"The data task requested can't be fulfilled {tap.name}.",
                        "input_params": None,
                        "alternative_fulfillable_data_task": ""
                    }
                }
                
                test_case_template = {
                    "data_task": test_case['data_task'],
                    "expected_output": {
                        "can_fulfill": False,
                        "input_params" : None
                    }
                }

                json_test_case_template = json.dumps(test_case_template, indent=4)
                logger.info("")
                logger.info("***** Test Case Template to copy in test_cases.json: *****")
                logger.info(json_test_case_template)
                logger.info("")

                json_example_template = json.dumps(example_template, indent=4)
                logger.info("")
                logger.info("***** Example Template to copy in tap-examples.json: *****")
                logger.info("(1) Check if one of inputCompatibility or outputCompatibility should be 'Yes', if so correct it")
                logger.info("(2) Customize explanation")
                logger.info("(3) Add a custom alternative_fulfillable_data_task")
                logger.info("")
                logger.info(json_example_template)
                logger.info("")


                logger.info(f'Test {i} PASSED.')
                self.results[i] = True
            else:
                logger.warning(f'Test {i} NOT PASSED.')
                self.results[i] = False
            return
        else:
            # data has been can_fulfilled, checking retriever validity
            retriever_validity = self.check_atomic_values(retriever_result.dict(), test_case['expected_output'], logger)
        if not retriever_validity:
            logger.warning(f'Test {i} NOT PASSED.')
            self.results[i] = False
            return
        else:                
            # generate example template
            example_template = {
                "title" : None,
                "public": True,
                "post_run_chat_message" : None,
                "data_task": test_case['data_task'],
                "final_json_response": {
                    "inputCompatibility": f"Only using the params provided {tap.name} INPUT SCHEMA: Yes, I am 100% sure that I can fulfill the params required by given task",
                    "outputCompatibility": f"Assuming data returned by {tap.name} is reliable and solely based on compatibility between DATA TASK and {tap.name} OUTPUT RETURN FIELDS: Yes, I am 100% sure that I can fulfill the given task given {tap.name} OUTPUT RETURN FIELDS",
                    "can_fulfill": True,
                    "explanation": f"The data task requested can be fulfilled: {tap.name} has the options to fulfill the given task. In input_params you can find the params needed to fulfill the given task.",
                    "input_params": retriever_result.retriever.input.body,
                    "alternative_fulfillable_data_task": None
                }
            }
            
            test_case_template = {
                "data_task": test_case['data_task'],
                "expected_output": {
                    "can_fulfill": True,
                    "input_params" : retriever_result.retriever.input.body,
                    "alternative_fulfillable_data_task": None
                }
            }
            
            tap._logger.info(f"***** Step 2. Testing retrieving sample data *****")
            try :
                final_data = tap.run_actor(retriever_result.retriever.input)
            except Exception as e:
                logger.error(f"An error occurred while retrieving sample data: {e}")
                logger.warning(f'Test {i} NOT PASSED.')
                self.results[i] = False
                return

            logger.info(f'Final Data Return: {final_data}')
            
            # Check if 'retriever', 'data_task', or 'body' are not present or if 'body' doesn't contain any parameters
            if 'retriever' not in test_case['expected_output'] or \
               'data_task' not in test_case['expected_output']['retriever'] or \
               'body' not in test_case['expected_output']['retriever']['data_task'] or \
               not test_case['expected_output']['retriever']['data_task']['body']:
                tap._logger.info(f"Fields are missing or body doesn't contain any parameters, skipping testing validation of final data.")

                json_test_case_template = json.dumps(test_case_template, indent=4)
                logger.info("")
                logger.info("***** Test Case Template to copy in test_cases.json: *****")
                logger.info("Remove from the input_params any field that is not needed to fulfill the given task (for example maxItems)")
                logger.info("")
                logger.info(json_test_case_template)
                logger.info("")

                json_example_template = json.dumps(example_template, indent=4)
                logger.info("")
                logger.info("***** Example Template to copy in tap-examples.json: *****")
                logger.info("Edit (remove it or set it differently) any input_params that may not to be related to the specif task (for example maxItems)")
                logger.info("")
                logger.info(json_example_template)
                logger.info("")
                # test has passed            
                logger.info(f'Test {i} PASSED.')

                self.results[i] = True
                return
            
            # check if sample_data contains at least 1 item
            if len(final_data) < 1:
                logger.warning(f'Test {i} NOT PASSED - The sample data contains less than 3 items.')
                self.results[i] = False
                return

            tap._logger.info(f"***** Step 3. Testing sample data validity *****")
            sample_data = tap.truncate_returned_data(final_data)
            logger.info(f'Sample Data: {sample_data}')

            # Validate data
            validate_data_return = tap.validate_data(test_case['data_task'], sample_data)
            logger.info(f'Validation Result: {validate_data_return}')

            json_test_case_template = json.dumps(test_case_template, indent=4)
            logger.info("")
            logger.info("***** Test Case Template to copy in test_cases.json: *****")
            logger.info("Remove from the input_params any field that is not required by the actor and it's not needed to fulfill the given task (for example maxItems)")
            logger.info("")
            logger.info(json_test_case_template)
            logger.info("")

            json_example_template = json.dumps(example_template, indent=4)
            logger.info("")
            logger.info("***** Example Template to copy in tap-examples.json: *****")
            logger.info("Edit (remove it or set it differently) any input_params that may not to be related to the specif task (for example maxItems)")
            logger.info("")
            logger.info(json_example_template)
            logger.info("")
            # test has passed            
            logger.info(f'Test {i} PASSED.')

            self.results[i] = True

    def test_webtap(self):
        '''
        This test runs in parallel all the test cases defined in the test_cases.json file.
        This is the main thread that will start all the other threads.
        '''

        apify_tap_id = os.environ["TESTRUN_APIFY_TAP_ID"]
        # Setting up main logger
        # if needed create a new directory for the logs of this tap
        if not files(__package__).joinpath('../logs', apify_tap_id).exists():
            files(__package__).joinpath('../logs', apify_tap_id).mkdir(parents=True, exist_ok=True)
        # Create a new directory with current date_time
        files(__package__).joinpath('../logs', apify_tap_id, self.current_date_time).mkdir(parents=True, exist_ok=True)
        self.logger_main_dir = files(__package__).joinpath('../logs', apify_tap_id, self.current_date_time)
        # Create a main.log file for logging the logic outside the threads
        main_log_filename = 'main.log'
        main_log = logging.getLogger('main')
        main_log.setLevel(logging.INFO)
        # Add handler to log to file
        main_fh = logging.FileHandler(self.logger_main_dir.joinpath(main_log_filename))
        main_log.addHandler(main_fh)
        # Add handler to log to standard output (stdout) as well
        stdout_handler = logging.StreamHandler()
        main_log.addHandler(stdout_handler)
        main_log.info('Starting tests...')

        self.tap = TapManager().get_tap(apify_tap_id)
        if self.tap is None:
            main_log.error(f"The given {apify_tap_id} Tap has not been found")
            return
 
        test_cases = self.tap.test_cases

        test_num = os.environ.get("TESTRUN_TEST_NUM", None)
        print(f'TESTRUN_TEST_NUM: {test_num}')
        main_log.info(f"Check logs in the directory: {str(self.logger_main_dir)}")
        if test_num is not None:
            main_log.info(f'Running single test {test_num}...')
            test_num = int(test_num)
            test_case = self.tap.test_cases[test_num]
            self.run_test(test_num, test_case)
        else:
            # existing code to run all tests
            main_log.info(f'Running {len(test_cases)} tests in parallel...')

            # check at least 1 test is present
            if len(test_cases) < 1:
                main_log.error(f"No tests have been found for {apify_tap_id}")
                return

            futures = []
            with ThreadPoolExecutor() as executor:
                for i, test_case in enumerate(test_cases):
                    main_log.info(f'Starting test {i}...')
                    future = executor.submit(self.run_test, i, test_case)
                    futures.append(future)
            # Wait for all tests to finish
            executor.shutdown(wait=True)
            # Check for exceptions
            for future in futures:
                try:
                    future.result()  # This will re-raise any exceptions
                except Exception as e:
                    main_log.error(f"An error occurred: {e}")
            #order results by i
            self.results = dict(sorted(self.results.items()))
            # print the result of each test
            for i, result in self.results.items():
                if result:
                    main_log.info(f'Test {i} PASSED.')
                else:
                    main_log.warning(f'Test {i} NOT PASSED.')
            # Continue with scoring logic
            # check if at least 1 test has been executed
            if len(self.results) < 1:
                main_log.error(f"No test has been executed")
                return
            score = sum(self.results.values()) / len(self.results) * 100
            main_log.info(f'Final score for this tap is: {score}/100 with {sum(self.results.values())} passed tests out of {len(self.results)}.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apify_tap_id', type=str, help='Apify Tap ID')
    parser.add_argument('--model', type=str, help='Wether to use gpt-3.5-turbo or gpt-4')
    parser.add_argument('--test_num', type=int, help='Number of the test to run')
    args = parser.parse_args()
    apify_tap_id = args.apify_tap_id
    model = args.model
    test_num = args.test_num
    print(f'Apify Tap ID: {apify_tap_id}')
    # check apify_tap_id is not None
    if apify_tap_id is None:
        print('Apify Tap ID, not set, make sure to set it with --apify_tap_id=id - Full example command python -m tests.apify_tap_test --apify_tap_id=tripadvisor --model=gpt-3.5-turbo')
        sys.exit(1)
    # check model is not None
    if model is None or (model != 'gpt-3.5-turbo' and model != 'gpt-4'):
        print('Model incorrect, must be one of gpt-3.5-turbo or gpt-4, make sure to set it with --model=model - Full example command python -m tests.apify_tap_test --apify_tap_id=tripadvisor --model=gpt-3.5-turbo')
        sys.exit(1)

    os.environ["TESTRUN_APIFY_TAP_ID"] = apify_tap_id
    os.environ["TESTRUN_MODEL"] = model
    if test_num is not None:
        os.environ["TESTRUN_TEST_NUM"] = str(test_num)
    # tells unittest to ignore the apify_tap_id and the model argument
    unittest.main(argv=['first-arg-is-ignored'], exit=False)