import uuid
import json
import random
import time
import requests
from collections import defaultdict

from pydantic import BaseModel


class Bus(BaseModel):
    plate: str
    company_id: int
    route_id: int
    bus_identifier: uuid.UUID


BUSES_ENDPOINT = "http://127.0.0.1:8001"
BUSES_LOCATION_ENDPOINT = "http://127.0.0.1:8002"

BUS_COMPANY_ID = 1

BUS_ROUTES = [
    {"route_name": "2411", "route_id": 1},
    {"route_name": "8105", "route_id": 2},
]


def get_bus_route_stops(bus_route_name: str):
    with open(f"bus_routes/{bus_route_name}.json") as file:
        data = json.load(file)
        stops = data[0]["stops"]
        return stops


def get_available_buses(route_id: int):
    url = BUSES_ENDPOINT + f"/bus-route/get-buses-from-route/?route_id={route_id}"
    request = requests.get(url)
    if request.status_code != 200:
        print("Error getting available buses")
        return []
    return request.json()


def create_bus_routes_data():
    bus_routes_data = defaultdict(dict)
    for bus_route in BUS_ROUTES:
        route_name = bus_route["route_name"]
        route_id = bus_route["route_id"]
        bus_routes_data[route_name]["stops"] = get_bus_route_stops(
            bus_route_name=route_name
        )
        bus_routes_data[route_name]["number_of_stops"] = len(
            bus_routes_data[route_name]["stops"]
        )
        bus_routes_data[route_name]["buses"] = get_available_buses(route_id=route_id)
    return bus_routes_data


def assign_random_starting_stop(bus_routes_data):
    for key in bus_routes_data.keys():
        for bus in bus_routes_data[key]["buses"]:
            random_stop = random.randrange(
                1, bus_routes_data[key]["number_of_stops"] - 1
            )
            bus["current_stop"] = random_stop
            bus["direction"] = random.choice(["forward", "backward"])


def update_stops(bus_routes_data):
    for key in bus_routes_data.keys():
        first_stop = 0
        last_stop = bus_routes_data[key]["number_of_stops"]
        for bus in bus_routes_data[key]["buses"]:
            if bus["current_stop"] == last_stop:
                bus["direction"] = "backward"
            elif bus["current_stop"] == first_stop:
                bus["direction"] = "forward"
            if bus["direction"] == "forward":
                bus["current_stop"] += 1
            else:
                bus["current_stop"] -= 1


def update_buses_location(bus_routes_data):
    for key in bus_routes_data.keys():
        for bus in bus_routes_data[key]["buses"]:
            bus_ = Bus(**bus)
            bus_location = bus_routes_data[key]["stops"][bus["current_stop"]]
            update_bus_location(
                bus=bus_,
                route_id=bus["route_id"],
                long=bus_location["lon"],
                lat=bus_location["lat"],
                stop_name=bus_location["name"],
            )


def update_bus_location(
    bus: Bus, route_id: int, long: float, lat: float, stop_name: str
):
    data = {
        "bus": {
            "bus_identifier": bus.bus_identifier.hex,
            "plate": bus.plate,
            "company_id": BUS_COMPANY_ID,
            "route_id": route_id,
        },
        "coordinates": {"type": "Point", "coordinates": [long, lat]},
        "stop_name": stop_name,
    }
    print(data)
    url = BUSES_LOCATION_ENDPOINT + "/bus-location/update/"
    request = requests.post(url, json=data)
    if request.status_code != 200:
        print("Error updating bus location for bus {bus.plate}")


def main():
    bus_routes_data = create_bus_routes_data()
    assign_random_starting_stop(bus_routes_data)
    for key in bus_routes_data.keys():
        print(key)
        print(
            f"Number of stops in route {key}: {bus_routes_data[key]["number_of_stops"]}"
        )
        print(f"Number of buses in route {key}: {len(bus_routes_data[key]["buses"])}")

    while True:
        print("Updating data")
        update_stops(bus_routes_data)
        update_buses_location(bus_routes_data)
        time.sleep(10)


if __name__ == "__main__":
    main()
