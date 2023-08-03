"""
Example usage of TripAdvisorTap from the Webtap library.

This example demonstrates how to instantiate the TripAdvisorTap,
load actor data, and retrieve data model
"""

# import necessary libraries
from webtap.taps.tripadvisor.tripadvisor import TripAdvisorTap
import logging

def tripadvisor_tap_example():
    """
    An example function demonstrating the use of TripAdvisorTap from the Webtap library.

    The function will:
    - Initialize the TripAdvisorTap
    - Log the actor name and the prompt template
    - Retrieve data for a specific model and log the returned data
    """

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    logging.info("Tripadvispr tap example")    

    # Initialize TripAdvisorTap
    trip_advisor_tap = TripAdvisorTap()

    # Get data for a specific data task
    data_task = "Hotels or vacation rentals in Paris, first week of September 2023, currency in EUR, language in Spanish, with email addresses"
    returnData = trip_advisor_tap.getDataModel(data_task)
    
    # Log the returned data
    logging.info("Tripadvisor tap return data: %s", returnData)

if __name__ == "__main__":
    tripadvisor_tap_example()