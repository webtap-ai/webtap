import argparse
from tools.tap_generator.tap_generator import TapGenerator


def run_example(actor_id):
    if not actor_id:
        print("Error: No actor_id provided.")
        print("Usage: python tap_generator_example.py <actor_id>")
        return

    tap_generator = TapGenerator(actor_id)
    tap_generator.generate_tap()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate TAP for a given actor.")
    parser.add_argument("actor_id", type=str, help="Actor ID to generate TAP for.")

    args = parser.parse_args()

    run_example(args.actor_id)
