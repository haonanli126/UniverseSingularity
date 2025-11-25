from us_core.systems.consciousness.global_workspace import (
    GlobalWorkspaceSystem,
    WorkspaceItem,
)


def test_global_workspace_selects_highest_score():
    gw = GlobalWorkspaceSystem()

    inputs = {
        "sensory": {
            "content": "看到红色物体",
            "newness": 1.0,
            "relevance": 1.0,
            "affect": 1.0,
            "goal_alignment": 1.0,
        },
        "memory": {
            "content": "很久以前的经历",
            "newness": 0.0,
            "relevance": 0.0,
            "affect": 0.0,
            "goal_alignment": 0.0,
        },
    }

    result = gw.compete_and_broadcast(inputs)
    assert result is not None
    assert result["source"] == "sensory"
    assert result["content"] == "看到红色物体"
    assert 0.0 <= result["score"] <= 1.0
    assert len(result["candidates"]) == 2


def test_global_workspace_respects_min_score_threshold():
    gw = GlobalWorkspaceSystem(min_score=0.9)

    inputs = {
        "low": {
            "content": "杂音",
            "newness": 0.1,
            "relevance": 0.1,
            "affect": 0.1,
            "goal_alignment": 0.1,
        }
    }

    result = gw.compete_and_broadcast(inputs)
    assert result is None
    assert gw.last_winner is None
