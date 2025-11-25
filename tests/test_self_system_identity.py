from datetime import datetime, timedelta

from us_core.systems.self.identity import (
    AutobiographicalMemory,
    LifeEvent,
    SelfIdentity,
    SelfNarrative,
)


def _t(offset_days: int = 0) -> datetime:
    base = datetime(2025, 1, 1, 12, 0, 0)
    return base + timedelta(days=offset_days)


def test_autobiographical_memory_orders_events_by_time():
    mem = AutobiographicalMemory()
    e2 = LifeEvent(timestamp=_t(1), description="second", tags=["work"], emotional_valence=0.1)
    e1 = LifeEvent(timestamp=_t(0), description="first", tags=["home"], emotional_valence=0.9)
    mem.add_event(e2)
    mem.add_event(e1)

    recent = mem.recent_events(2)
    assert [e.description for e in recent] == ["first", "second"]


def test_events_by_tag_filters_correctly():
    mem = AutobiographicalMemory()
    mem.add_event(LifeEvent(timestamp=_t(0), description="helped friend", tags=["care"], emotional_valence=0.8))
    mem.add_event(LifeEvent(timestamp=_t(0), description="finished task", tags=["work"], emotional_valence=0.2))

    care_events = mem.events_by_tag("care")
    assert len(care_events) == 1
    assert care_events[0].description == "helped friend"


def test_self_narrative_summarises_events():
    mem = AutobiographicalMemory()
    mem.add_event(LifeEvent(timestamp=_t(0), description="start", tags=["init"], emotional_valence=0.0))
    mem.add_event(LifeEvent(timestamp=_t(1), description="progress", tags=["work"], emotional_valence=0.5))

    narrative = SelfNarrative().summarise(mem)
    assert "2 条关键经历" in narrative
    assert "start" in narrative
    assert "progress" in narrative


def test_self_identity_updates_core_traits_and_summary():
    mem = AutobiographicalMemory()
    mem.add_event(
        LifeEvent(
            timestamp=_t(0),
            description="helped friend",
            tags=["care"],
            emotional_valence=0.9,
        )
    )
    identity = SelfIdentity(core_traits=["curious"])

    identity.update_from_memory(mem)

    assert any(t in identity.core_traits for t in ("caring", "resilient"))
    assert identity.last_updated is not None
    assert identity.last_summary is not None
    assert "helped friend" in identity.last_summary
