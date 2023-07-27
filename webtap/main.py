from plugins.tripadvisor.tripadvisor_actor import ApifyActorTripadvisor
from plugins.tripadvisor.tripadvisor_tap import TapTripadvisor

def main():
    tripadvisorActor = ApifyActorTripadvisor()
    print("Tripadvisor Actor")
    print( tripadvisorActor )

    print("------------------")

    print("Tripadvisor Tap")
    tripadvisorTap = TapTripadvisor()
    print( tripadvisorTap )

if __name__ == "__main__":
    main()