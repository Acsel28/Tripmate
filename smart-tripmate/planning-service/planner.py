from datetime import datetime


def parse_dates(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if end <= start:
        raise ValueError("end_date must be after start_date")
    return start, end


def calculate_total_cost(travel_cost, stay_cost, activity_cost, buffer_ratio=0.1):
    subtotal = float(travel_cost) + float(stay_cost) + float(activity_cost)
    return round(subtotal + (subtotal * float(buffer_ratio)), 2)


def is_affordable(total_cost, budget):
    return float(total_cost) <= float(budget)


def pick_cheapest(items, price_key="price"):
    if not items:
        return None
    return min(items, key=lambda x: x.get(price_key, 0))


def pick_fastest(items):
    if not items:
        return None
    return min(items, key=lambda x: x.get("duration", 10**9))


def pick_balanced(items):
    if not items:
        return None
    return min(items, key=lambda x: (x.get("price", 0) * 0.7) + (x.get("duration", 0) * 0.3))


def generate_plans(options, nights, budget, preference_transport=None):
    travel_pool = options.get("flights", []) + options.get("trains", [])
    if preference_transport == "flight":
        travel_pool = options.get("flights", []) or travel_pool
    if preference_transport == "train":
        travel_pool = options.get("trains", []) or travel_pool

    hotels = options.get("hotels", [])
    activities = options.get("activities", [])

    activity_cost = sum(a.get("price", 0) for a in activities[:2])

    templates = {
        "cheapest": (pick_cheapest(travel_pool), pick_cheapest(hotels, "price_per_night")),
        "fastest": (pick_fastest(travel_pool), pick_cheapest(hotels, "price_per_night")),
        "balanced": (pick_balanced(travel_pool), pick_balanced([{"price": h.get("price_per_night", 0), **h} for h in hotels])),
    }

    plans = []
    for name, (travel, hotel) in templates.items():
        if not travel or not hotel:
            continue
        stay_cost = hotel.get("price_per_night", 0) * nights
        total_cost = calculate_total_cost(travel.get("price", 0), stay_cost, activity_cost)
        plans.append(
            {
                "plan_type": name,
                "travel": travel,
                "hotel": hotel,
                "activity_cost": activity_cost,
                "total_cost": total_cost,
                "affordability": "affordable" if is_affordable(total_cost, budget) else "not affordable",
            }
        )

    return plans


def build_suggestions(plans, budget):
    if any(p["affordability"] == "affordable" for p in plans):
        return []
    return [
        "Reduce trip duration by 1-2 days to lower hotel cost.",
        "Switch to train or lower-cost transport option.",
        "Choose a budget hotel category.",
        "Remove expensive activities from itinerary.",
    ]
