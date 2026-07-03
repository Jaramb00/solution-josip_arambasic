"""Unit testovi za transformaciju DummyJSON -> Ticket (čiste funkcije, bez mreže)."""

import pytest

from tickethub.services.dummyjson import compute_priority, compute_status, transform_todo


@pytest.mark.parametrize(
    ("todo_id", "expected"),
    [(3, "low"), (1, "medium"), (2, "high"), (6, "low"), (150, "low")],
)
def test_compute_priority(todo_id, expected):
    assert compute_priority(todo_id) == expected


def test_compute_status():
    assert compute_status(True) == "closed"
    assert compute_status(False) == "open"


def test_transform_todo_maps_all_fields():
    todo = {"id": 5, "todo": "Solve a Rubik's cube", "completed": True, "userId": 42}
    usernames = {42: "emilys"}

    row = transform_todo(todo, usernames)

    assert row == {
        "id": 5,
        "title": "Solve a Rubik's cube",
        "status": "closed",
        "priority": "high",  # 5 % 3 == 2
        "assignee": "emilys",
        "source": todo,
    }


def test_transform_todo_unknown_user_gives_none_assignee():
    todo = {"id": 1, "todo": "X", "completed": False, "userId": 999}
    assert transform_todo(todo, {})["assignee"] is None
