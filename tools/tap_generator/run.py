import argparse, json
from pathlib import Path
from tools.tap_generator.tap_generator import TapGenerator

"""
example url: https://www.apify.com/shanes/tweet-flash
example actor_id: shanes/tweet-flash
"""


def extract_actor_id_from_url(url):
    return url.replace("https://apify.com/", "")


def run_example(actor_id):
    if not actor_id:
        print("Error: No actor_id provided.")
        print("Usage: python tap_generator_example.py <actor_id>")
        print("Example: python tap_generator_example.py shanes/tweet-flash")
        return

    tap_generator = TapGenerator(actor_id)
    tap_generator.generate_tap()


def run_url_lists():
    # load array from json file data/tap_generator/generator_run/url_list.json
    url_list_file = (
        Path(__file__).parent.parent.parent
        / "data/tap_generator/generator_run/url_list.json"
    )
    results_file = (
        Path(__file__).parent.parent.parent
        / "data/tap_generator/results/actor_results.json"
    )

    with open(url_list_file) as f:
        url_list = json.load(f)

    with open(results_file) as f:
        results = json.load(f)

    i = 0
    for url in url_list:
        for key, value in url.items():
            i += 1
            actor_id = extract_actor_id_from_url(value)
            # Print a message that you are generating the tap for the actor, add decoration to make it look clear that a new tap is starting (e.g. add lots of newlines or --- or something)
            print("--------------------------------------------------")
            print("--------------------------------------------------")
            print("--------------------------------------------------")
            print(f"## ({i}/{len(url_list)}) : Generating tap for - {actor_id}")
            print("--------------------------------------------------")
            print("--------------------------------------------------")
            print("--------------------------------------------------")
            try:
                # check if actor_id is already a key in results object
                if actor_id in results:
                    print(f"Tap already generated for {key}")
                    continue
                tap_generator = TapGenerator(actor_id)
                tap_generator.generate_tap()
                print(f"Successfully generated tap for {key}")
            except Exception as e:
                error_message = f"Exiting while running tap generator on tap tap for {key} ({i}/{len(url_list)}) - {actor_id}. Error: {str(e)};"
                print(f"Failed to generate tap for {key}")
                print(error_message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate TAP for a given actor.")
    parser.add_argument(
        "actor_id",
        type=str,
        nargs="?",
        default=None,
        help="Actor ID to generate TAP for.",
    )

    args = parser.parse_args()

    if args.actor_id:
        run_example(args.actor_id)
    else:
        run_url_lists()
