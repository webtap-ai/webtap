from webtap.taps.tripadvisor.tripadvisor import TripAdvisorTap
import logging

def main():

    logging.basicConfig(level=logging.INFO)

    trip_advisor_tap = TripAdvisorTap()
    returnData = trip_advisor_tap.getDataModel( "hello world")
    print("Return data: ", returnData)

if __name__ == "__main__":
    main()
