from typing import Any


def parse_cost(value: Any) -> float:
    try:
        return float(str(value or "").strip().replace("$", ""))
    except ValueError:
        return 0.0


def format_cost(value: float) -> str:
    if value <= 0:
        return ""
    return f"${value:.6f}"


def total_result_cost(results: list[dict[str, Any]]) -> float:
    return round(sum(parse_cost(result.get("llm_cost", 0)) for result in results), 8)
