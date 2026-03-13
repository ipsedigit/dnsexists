import re


def fetch(args: dict) -> list[dict]:
    return [
        {"name": "fastapi", "stars": 75000, "url": "https://github.com/tiangolo/fastapi"},
        {"name": "pydantic", "stars": 20000, "url": "https://github.com/pydantic/pydantic"},
        {"name": "httpx", "stars": 13000, "url": "https://github.com/encode/httpx"},
        {"name": "rich", "stars": 48000, "url": "https://github.com/Textualize/rich"},
        {"name": "typer", "stars": 15000, "url": "https://github.com/tiangolo/typer"},
    ]


def select(candidates: list[dict]) -> list[str]:
    results = []
    for item in candidates:
        name = item["name"].lower()
        name = re.sub(r"[^a-z0-9-]", "-", name)
        name = name.strip("-")
        if name:
            results.append(name)
    return results
