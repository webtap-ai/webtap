from tools.tap_generator.tap_generator import TapGenerator

def run_example():
    tap_generator = TapGenerator('petr_cermak/yellow-pages-scraper')
    tap_generator.generate_tap()

if __name__ == "__main__":
    run_example()