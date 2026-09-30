"""Service-interval checks for the Vossberg Mobility fleet."""

SERVICE_INTERVAL_KM = 15000
WARN_AT_PERCENT = 80


def wear_percent(km_since_service: int | float, interval: int | float) -> float:
    """Return the percentage of a service interval already used."""
    return km_since_service / interval * 100


def needs_service(car: dict) -> bool:
    """Return whether a car has reached the service warning threshold."""
    last = car.get("last_service_km")
    if last is None:
        return False

    km_since = car["odometer"] - last
    return wear_percent(km_since, SERVICE_INTERVAL_KM) >= WARN_AT_PERCENT


def check_fleet(fleet: list[dict]) -> list[str]:
    """Return IDs of cars due for service and print each flagged ID."""
    flagged: list[str] = []
    for car in fleet:
        if needs_service(car):
            flagged.append(car["id"])
            print(f"SERVICE DUE: {car['id']}")
    return flagged
