from __future__ import annotations

from pathlib import Path

from soa.memory import LongTermMemory, Memory, WorkingMemory


def test_working_memory_set_get_delete_and_clear():
    working = WorkingMemory()
    assert len(working) == 0
    working.set("token", "abc")
    assert "token" in working
    assert working.get("token") == "abc"
    assert working.get("missing", "nope") == "nope"
    assert working.items() == {"token": "abc"}
    assert working.delete("token") is True
    assert working.delete("token") is False
    working.set("a", 1)
    working.clear()
    assert len(working) == 0


def test_long_term_remember_and_recall():
    store = LongTermMemory()
    store.remember("the sky is blue", tags=("color",))
    store.remember("grass is green", tags=("color",))
    assert len(store) == 2
    hits = store.recall("sky")
    assert [fact.text for fact in hits] == ["the sky is blue"]
    by_tag = store.recall("color")
    assert len(by_tag) == 2
    assert store.recall("") == store.all_facts()
    store.clear()
    assert len(store) == 0


def test_blank_fact_is_not_stored():
    store = LongTermMemory()
    fact = store.remember("   ")
    assert fact.text == ""
    assert len(store) == 0


def test_long_term_memory_persists_to_json(tmp_path: Path):
    path = tmp_path / "facts.json"
    first = LongTermMemory(path)
    first.remember("apples are fruit", tags=("food",))
    second = LongTermMemory(path)
    hits = second.recall("apples")
    assert len(hits) == 1
    assert hits[0].tags == ("food",)


def test_memory_facade_delegates():
    memory = Memory()
    memory.working.set("step", 1)
    memory.remember("nights are dark")
    assert memory.working.get("step") == 1
    assert memory.recall("nights")[0].text == "nights are dark"
