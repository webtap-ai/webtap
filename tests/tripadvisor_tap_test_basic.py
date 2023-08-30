import unittest
from webtap.taps.apify_tap import ActorInput, ActorParameters, ApifyDataRetrieverModel, ApifyRetrieverResult
from webtap.taps.tripadvisor_custom_tap import TripAdvisorCustomTap

'''
This is a basic test for the TripAdvisorCustomTap class.
It runs only one single test case.
'''

class TestApifyTap(unittest.TestCase):

    def setUp(self):
        self.tripadvisor_tap = TripAdvisorCustomTap()

    def test_getDataModel(self):
        data_task = "Hotels or vacation rentals in Paris, first week of September 2023, currency in EUR, language in Spanish, with email addresses"
        expected_return = ApifyRetrieverResult(
            can_fulfill=True, 
            explanation='The given task can be fulfilled using the params provided in Tripadvisor Scraper INPUT SCHEMA and Tripadvisor Scraper OUTPUT RETURN FIELDS.', 
            retriever=ApifyDataRetrieverModel(
                type='apify', 
                id='maxcopell~tripadvisor', 
                input=ActorInput(
                    parameters=ActorParameters(actorId='maxcopell~tripadvisor'), 
                    body={
                        'checkInDate': '2023-09-01', 
                        'checkOutDate': '2023-09-07', 
                        'currency': 'EUR', 
                        'includeAttractions': False, 
                        'includeHotels': True, 
                        'includePriceOffers': True, 
                        'includeRestaurants': False, 
                        'includeTags': True, 
                        'includeVacationRentals': True, 
                        'language': 'es', 
                        'locationFullName': 'Paris', 
                        'maxItems': 0, 
                        'proxyConfiguration': {'useApifyProxy': True}
                    }
                )
            ), 
            alternative_fulfillable_data_task=None
        )
        result = self.tripadvisor_tap.getDataModel(data_task)
        self.assertEqual(result, expected_return)

if __name__ == '__main__':
    unittest.main()
