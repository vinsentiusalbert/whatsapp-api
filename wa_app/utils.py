import json


def normalize_phone(phone: str | None) -> str:
    if not phone:
        return ""
    return (
        str(phone)
        .replace("+", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )


def safe_json_dumps(data) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def clamp_limit(limit: int, minimum: int = 1, maximum: int = 1000) -> int:
    return max(minimum, min(limit, maximum))
