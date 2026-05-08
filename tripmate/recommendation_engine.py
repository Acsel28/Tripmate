def build_recommendations(payload):
    destination = payload["destination_city"]
    budget = float(payload["budget"])
    preferences = payload.get("preferences", {})
    activity_level = preferences.get("activity_level", "medium")

    ideas = [
        {
            "title": f"Budget-friendly {destination} arrival window",
            "detail": "Leave early morning to unlock lower transport fares and a full first day.",
            "type": "timing",
        },
        {
            "title": f"{destination} stay strategy",
            "detail": "Pick hotels near public transport hubs to reduce local transfer costs.",
            "type": "stay",
        },
    ]

    if budget < 900:
        ideas.append(
            {
                "title": "Lean budget mode",
                "detail": "Keep one signature activity and fill the rest with free local experiences.",
                "type": "budget",
            }
        )
    if activity_level == "high":
        ideas.append(
            {
                "title": "Activity pacing",
                "detail": "Cluster paid activities on two days and keep one low-cost recovery day.",
                "type": "activities",
            }
        )

    return ideas
