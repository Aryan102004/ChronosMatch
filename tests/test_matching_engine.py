from cython_engine.matching_engine import CythonMatchingEngine


def test_matching_engine_creation():
    engine = CythonMatchingEngine()

    assert engine.get_buy_order_count() == 0
    assert engine.get_sell_order_count() == 0


def test_matching_engine_add_orders():
    engine = CythonMatchingEngine()

    engine.add_order(
        1,
        100.0,
        50,
        False,
        1
    )

    engine.add_order(
        2,
        99.0,
        40,
        True,
        2
    )

    assert engine.get_sell_order_count() == 1
    assert engine.get_buy_order_count() == 1


def test_matching_engine_full_match():
    engine = CythonMatchingEngine()

    engine.add_order(
        1,
        100.0,
        50,
        False,
        1
    )

    trades = engine.match_order(
        2,
        100.0,
        50,
        True,
        2
    )

    assert len(trades) == 1

    assert trades[0]["buy_order_id"] == 2
    assert trades[0]["sell_order_id"] == 1
    assert trades[0]["price"] == 100.0
    assert trades[0]["quantity"] == 50

    assert engine.get_sell_order_count() == 0
    assert engine.get_buy_order_count() == 0


def test_matching_engine_partial_fill():
    engine = CythonMatchingEngine()

    engine.add_order(
        1,
        100.0,
        50,
        False,
        1
    )

    trades = engine.match_order(
        2,
        100.0,
        80,
        True,
        2
    )

    assert len(trades) == 1

    assert trades[0]["quantity"] == 50

    assert engine.get_sell_order_count() == 0
    assert engine.get_buy_order_count() == 1


def test_matching_engine_cancel():
    engine = CythonMatchingEngine()

    engine.add_order(
        1,
        100.0,
        50,
        False,
        1
    )

    assert engine.get_sell_order_count() == 1

    result = engine.cancel_order(1)

    assert result is True
    assert engine.get_sell_order_count() == 0