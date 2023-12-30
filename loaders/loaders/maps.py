from pathlib import Path

from googlemaps import Client

key = Path("/etc/secrets/maps-api-key").read_text(encoding="utf-8").strip()

CLIENT = Client(key=key)


def get_lat_lng(address: str) -> tuple[float, float]:
    location = CLIENT.geocode(address=address, components={"country": "GR"})[0][
        "geometry"
    ]["location"]
    return location["lat"], location["lng"]
