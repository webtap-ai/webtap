import unittest
from webtap.apify_tap.apify_tap import ActorInput, ActorParameters, ApifyDataModel, ApifyTapReturn
from webtap.taps.tripadvisor.tripadvisor import TripAdvisorTap

class TestApifyTap(unittest.TestCase):

    def setUp(self):
        self.tripadvisor_tap = TripAdvisorTap()

    def test_getDataModel(self):
        data_task = "Hotels or vacation rentals in Paris, first week of September 2023, currency in EUR, language in Spanish, with email addresses"
        expected_return = ApifyTapReturn(
            can_deliver=True, 
            explanation='The given task can be fulfilled using the params provided in Tripadvisor Scraper INPUT SCHEMA and Tripadvisor Scraper OUTPUT RETURN FIELDS.', 
            data_model=ApifyDataModel(
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
                        'proxyConfiguration': {'useApifyProxy': False}
                    }
                )
            ), 
            alternative_fulfillable_data_request=None
        )
        result = self.tripadvisor_tap.getDataModel(data_task)
        self.assertEqual(result, expected_return)

if __name__ == '__main__':
    unittest.main()
