"""Klijent za DummyJSON izvor + transformacija u vlastiti Ticket model."""

from typing import Any

import httpx

from tickethub.config import settings

# id % 3 -> priority
_PRIORITY_BY_REMAINDER = {0: "low", 1: "medium", 2: "high"}


def compute_priority(todo_id: int) -> str:
    """priority: izračunato iz id % 3 -> low/medium/high."""
    return _PRIORITY_BY_REMAINDER[todo_id % 3]


def compute_status(completed: bool) -> str:
    """status: 'closed' ako je completed == true, inače 'open'."""
    return "closed" if completed else "open"


def transform_todo(todo: dict[str, Any], usernames: dict[int, str]) -> dict[str, Any]:
    """Transformira DummyJSON 'todo' u redak Ticket modela."""
    todo_id = int(todo["id"])
    user_id = todo.get("userId")
    return {
        "id": todo_id,
        "title": todo["todo"],
        "status": compute_status(bool(todo.get("completed", False))),
        "priority": compute_priority(todo_id),
        "assignee": usernames.get(user_id),
        "source": todo,
    }


async def fetch_todos(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    resp = await client.get("/todos", params={"limit": 0})
    resp.raise_for_status()
    return resp.json()["todos"]


async def fetch_usernames(client: httpx.AsyncClient) -> dict[int, str]:
    resp = await client.get("/users", params={"limit": 0, "select": "username"})
    resp.raise_for_status()
    return {int(u["id"]): u["username"] for u in resp.json()["users"]}


async def fetch_tickets() -> list[dict[str, Any]]:
    """Dohvati todo-e i korisnike te vrati listu transformiranih Ticket redaka."""
    async with httpx.AsyncClient(
        base_url=settings.dummyjson_base_url, timeout=settings.http_timeout
    ) as client:
        usernames = await fetch_usernames(client)
        todos = await fetch_todos(client)
    return [transform_todo(todo, usernames) for todo in todos]