"""Build and print the nightly Vossberg Mobility fleet-health report."""

from config_loader import get_setting, load_settings
import fleet_utils
from km_wachter import SERVICE_INTERVAL_KM, needs_service, wear_percent
from log_util import flush_log, log


def car_wear(car: dict) -> float | None:
    """Return wear percentage, or None when the service reading is missing."""
    last = car.get("last_service_km")
    if last is None:
        return None

    return wear_percent(car["odometer"] - last, SERVICE_INTERVAL_KM)


def fleet_summary(fleet: list[dict]) -> dict:
    """Return fleet count, due count, and average wear for valid readings."""
    wear_values: list[float] = []
    due = 0

    for car in fleet:
        wear = car_wear(car)
        if wear is not None:
            wear_values.append(wear)

        if needs_service(car):
            due += 1

    average = sum(wear_values) / len(wear_values) if wear_values else 0.0
    return {
        "count": len(fleet),
        "due": due,
        "average_wear": average,
    }


def print_report(fleet: list[dict]) -> None:
    """Print the fleet report and flush its log entry."""
    settings = load_settings()
    log(get_setting(settings, "report_title", "Nightly fleet report"))
    summary = fleet_summary(fleet)

    print(f"Fleet: {summary['count']} cars")
    print(f"Due for service: {summary['due']}")
    print(f"Average wear: {summary['average_wear']:.1f}%")

    total_km = sum(car["odometer"] for car in fleet)
    miles = fleet_utils.km_to_miles(total_km)
    print(f"Fleet distance: {fleet_utils.format_number(miles)} miles")
    flush_log(get_setting(settings, "log_file", "km_wachter.log"))
