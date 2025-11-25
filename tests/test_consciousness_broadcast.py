from us_core.systems.consciousness.broadcast import BroadcastSystem


def test_broadcast_delivers_to_all_subscribers():
    system = BroadcastSystem()
    received_1 = []
    received_2 = []

    system.subscribe("s1", lambda msg: received_1.append(msg))
    system.subscribe("s2", lambda msg: received_2.append(msg))

    message = {"content": "hello"}
    count = system.broadcast(message)

    assert count == 2
    assert received_1[0] is message
    assert received_2[0] is message


def test_unsubscribe_removes_subscriber():
    system = BroadcastSystem()
    calls = []

    system.subscribe("s1", lambda msg: calls.append("s1"))
    system.subscribe("s2", lambda msg: calls.append("s2"))

    system.unsubscribe("s1")
    system.broadcast({"x": 1})

    assert calls == ["s2"]
    assert system.subscriber_count == 1
