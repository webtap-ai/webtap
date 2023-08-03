from webtap.taps.tripadvisor.tripadvisor import TripAdvisorTap
import logging

def main():

    logging.basicConfig(level=logging.DEBUG)    

    trip_advisor_tap = TripAdvisorTap()
    print("Actor name: ")
    print(trip_advisor_tap.apfiy_tap_actor.actor.name)

    print("Prompt template: ", trip_advisor_tap.prompt_template)

    returnData = trip_advisor_tap.getDataModel( "Hotels or vacation rentals in Paris, first week of September 2023, currency in EUR, language in Spanish, with email addresses")
    print("Return data: ", returnData)


if __name__ == "__main__":
    main()
