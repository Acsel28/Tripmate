from planning_engine import PlanningError, parse_trip_dates


TRANSPORT_MULTIPLIERS = {
    "flight": {"base": 190, "speed": 2.4},
    "train": {"base": 110, "speed": 5.6},
    "bus": {"base": 70, "speed": 8.0},
}


HOTEL_TIERS = [
    {"name": "Metro Capsule Hub", "price_per_night": 55, "rating": 3.9, "tier": "economy"},
    {"name": "TripMate City Suites", "price_per_night": 92, "rating": 4.3, "tier": "balanced"},
    {"name": "Skyline Grand", "price_per_night": 160, "rating": 4.8, "tier": "premium"},
]


def build_booking_catalog(source_city, destination_city, start_date, end_date, traveler_count):
    _, _, trip_days = parse_trip_dates(start_date, end_date)
    if source_city.strip().lower() == destination_city.strip().lower():
        raise PlanningError("Source and destination cannot be the same.")

    if destination_city.strip().lower() in {"nowhere", "atlantis"}:
        return {"transport": [], "hotels": [], "activities": []}

    traveler_count = max(int(traveler_count), 1)
    route_seed = len(source_city.strip()) + len(destination_city.strip())
    transport = []
    for mode, config in TRANSPORT_MULTIPLIERS.items():
        total = round((config["base"] + route_seed * 2.75) * traveler_count, 2)
        transport.append(
            {
                "mode": mode,
                "provider": f"{destination_city.title()} {mode.title()} Line",
                "price_total": total,
                "duration_hours": round(config["speed"] + route_seed / 12, 1),
            }
        )

    hotels = []
    for hotel in HOTEL_TIERS:
        hotels.append(
            {
                "name": f"{destination_city.title()} {hotel['name']}",
                "price_per_night": round(hotel["price_per_night"] + route_seed / 3, 2),
                "rating": hotel["rating"],
                "tier": hotel["tier"],
            }
        )

    activities = [
        {"name": f"{destination_city.title()} walking tour", "estimated_cost": 20 * traveler_count},
        {"name": f"{destination_city.title()} food trail", "estimated_cost": 35 * traveler_count},
        {"name": f"{destination_city.title()} museum pass", "estimated_cost": 18 * traveler_count},
    ]

    return {"transport": transport, "hotels": hotels, "activities": activities, "trip_days": trip_days}
