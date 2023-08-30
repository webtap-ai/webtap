import json
import unittest
import logging
import os
from importlib.resources import files
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from webtap.tap_manager import TapManager

'''
    This is a full test (run 10 tests in parallel) for the TripAdvisorCustomTap class.
'''

class TestWebtap(unittest.TestCase):

    current_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")

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
        fh = logging.FileHandler(files(__package__).joinpath('../logs', self.current_date_time, log_filename))
        logger.addHandler(fh)
        self.loggers.append(logger)

        logger.info(f'Running test {i}...')
        logger.info(f'Input: {test_case["input"]}')

        self.tripadvisor_tap = TapManager().get_tap("tripadvisor")
        # Set the logger of tripadvisor_tap to the main logger
        self.tripadvisor_tap._logger = logger

        result = self.tripadvisor_tap.get_retriever(test_case['input']).dict()
        logger.info(f'Output: {result}')
        final_result = self.check_atomic_values(result, test_case['expected_output'], logger)
        if final_result:
            logger.info(f'Test {i} PASSED.')
        else:
            logger.warning(f'Test {i} NOT PASSED.')
        self.results[i] = final_result

    def test_webtap(self):
        '''
        This test runs in parallel all the test cases defined in the test_cases.json file.
        This is the main thread that will start all the other threads.
        '''
        # Setting up main logger
        # Create a new directory with current date_time
        files(__package__).joinpath('../logs', self.current_date_time).mkdir(parents=True, exist_ok=True)
        # Create a main.log file for logging the logic outside the threads
        main_log_filename = 'main.log'
        main_log = logging.getLogger('main')
        main_log.setLevel(logging.INFO)
        # Add handler to log to file
        main_fh = logging.FileHandler(files(__package__).joinpath('../logs', self.current_date_time, main_log_filename))
        main_log.addHandler(main_fh)
        # Add handler to log to standard output (stdout) as well
        stdout_handler = logging.StreamHandler()
        main_log.addHandler(stdout_handler)
        main_log.info('Starting tests...')

        self.tripadvisor_tap = TapManager().get_tap("tripadvisor")
        test_cases = self.tripadvisor_tap.test_cases
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
        score = sum(self.results.values()) / len(self.results) * 100
        main_log.info(f'Final score for this tap is: {score}/100 with {sum(self.results.values())} passed tests out of {len(self.results)}.')

if __name__ == '__main__':
    unittest.main()