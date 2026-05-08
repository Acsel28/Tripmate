import json
from datetime import datetime


DATE_FORMAT = "%Y-%m-%d"


class PlanningError(ValueError):
    pass


def parse_trip_dates(start_date, end_date):
    try:
        start = datetime.strptime(start_date, DATE_FORMAT).date()
        end = datetime.strptime(end_date, DATE_FORMAT).date()
    except ValueError as exc:
        raise PlanningError("Dates must use YYYY-MM-DD format.") from exc

    if end < start:
        raise PlanningError("End date must be on or after start date.")

    trip_days = (end - start).days + 1
    if trip_days <= 0:
        raise PlanningError("Trip must be at least one day long.")

    return start, end, trip_days


def estimate_activity_cost(trip_days, traveler_count, activity_level):
    level_map = {
        "low": 25,
        "medium": 45,
        "high": 75,
    }
    per_day = level_map.get((activity_level or "medium").lower(), 45)
    return round(per_day * trip_days * traveler_count, 2)


def calculate_total_cost(transport_cost, hotel_cost, activity_cost, buffer_rate=0.12):
    subtotal = float(transport_cost) + float(hotel_cost) + float(activity_cost)
    buffer_cost = round(subtotal * buffer_rate, 2)
    return round(subtotal + buffer_cost, 2), buffer_cost


def determine_affordability(total_cost, budget):
    return float(total_cost) <= float(budget)


def generate_suggestions(total_cost, budget, cheapest_option, trip_days, traveler_count):
    suggestions = []
    over_by = round(float(total_cost) - float(budget), 2)

    if over_by <= 0:
        if cheapest_option["hotel"]["price_per_night"] > 90:
            suggestions.append("Swap to a budget hotel tier to create more spending room.")
        if trip_days > 4:
            suggestions.append("Move one expensive activity to a free walking or museum day.")
        suggestions.append("Lock transport early to avoid fare spikes.")
        return suggestions

    if trip_days > 2:
        suggestions.append("Reduce the trip by 1-2 days to lower hotel and activity costs.")
    if cheapest_option["transport"]["mode"] != "bus":
        suggestions.append("Switch to the lowest-cost transport option for a cheaper plan.")
    if cheapest_option["hotel"]["price_per_night"] > 75:
        suggestions.append("Choose the economy hotel option to cut nightly stay costs.")
    if traveler_count > 2:
        suggestions.append("Trim paid activities and prioritize group discounts.")
    suggestions.append(f"Current plan exceeds budget by {over_by:.2f}.")
    return suggestions


def rank_plan(option, mode):
    cost = option["cost_breakdown"]["total_cost"]
    duration = option["transport"]["duration_hours"]
    hotel_rating = option["hotel"]["rating"]

    if mode == "cheapest":
        return (cost, duration, -hotel_rating)
    if mode == "fastest":
        return (duration, cost, -hotel_rating)
    return (abs(cost - option["target_budget"]), duration, cost)


def build_plan_variants(request_payload, booking_options):
    _, _, trip_days = parse_trip_dates(request_payload["start_date"], request_payload["end_date"])

    transport_options = booking_options.get("transport", [])
    hotel_options = booking_options.get("hotels", [])
    if not transport_options:
        raise PlanningError("No travel routes are available for the selected trip.")
    if not hotel_options:
        raise PlanningError("No hotel options are available for the selected destination.")

    traveler_count = int(request_payload.get("traveler_count", 1))
    activity_cost = estimate_activity_cost(
        trip_days,
        traveler_count,
        request_payload.get("preferences", {}).get("activity_level"),
    )
    target_budget = float(request_payload["budget"])

    candidates = []
    for transport in transport_options:
        for hotel in hotel_options:
            hotel_total = round(hotel["price_per_night"] * max(trip_days - 1, 1), 2)
            total_cost, buffer_cost = calculate_total_cost(
                transport["price_total"],
                hotel_total,
                activity_cost,
            )
            candidates.append(
                {
                    "target_budget": target_budget,
                    "transport": transport,
                    "hotel": hotel,
                    "activities": {
                        "activity_level": request_payload.get("preferences", {}).get("activity_level", "medium"),
                        "estimated_cost": activity_cost,
                    },
                    "cost_breakdown": {
                        "transport": round(float(transport["price_total"]), 2),
                        "hotel": hotel_total,
                        "activities": activity_cost,
                        "buffer": buffer_cost,
                        "total_cost": total_cost,
                    },
                }
            )

    cheapest_option = min(candidates, key=lambda item: item["cost_breakdown"]["total_cost"])
    plans = {}
    for mode in ("cheapest", "fastest", "balanced"):
        selected = min(candidates, key=lambda item: rank_plan(item, mode))
        total_cost = selected["cost_breakdown"]["total_cost"]
        plans[mode] = {
            "plan_type": mode,
            "title": f"{mode.title()} {request_payload['destination_city']} plan",
            "affordable": determine_affordability(total_cost, target_budget),
            "summary": {
                "source_city": request_payload["source_city"],
                "destination_city": request_payload["destination_city"],
                "trip_days": trip_days,
                "traveler_count": traveler_count,
            },
            "transport": selected["transport"],
            "hotel": selected["hotel"],
            "activities": selected["activities"],
            "cost_breakdown": selected["cost_breakdown"],
            "suggestions": generate_suggestions(
                total_cost,
                target_budget,
                cheapest_option,
                trip_days,
                traveler_count,
            ),
        }

    return {
        "request": request_payload,
        "plans": plans,
        "trip_days": trip_days,
        "cheaper_alternatives": [
            {
                "type": "transport",
                "message": f"Try {cheapest_option['transport']['mode']} {cheapest_option['transport']['provider']} for the lowest fare.",
            },
            {
                "type": "hotel",
                "message": f"{min(hotel_options, key=lambda item: item['price_per_night'])['name']} is the lowest nightly hotel option.",
            },
        ],
    }


def serialize_payload(payload):
    return json.dumps(payload)
