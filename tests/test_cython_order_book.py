from cython_engine.order_book import CythonOrder, CythonOrderBook


def test_cython_order_creation():
    order = CythonOrder(
        1,
        100.0,
        50,
        True,
        1
    )

    assert order.order_id == 1
    assert order.price == 100.0
    assert order.quantity == 50
    assert order.is_buy is True
    assert order.timestamp == 1


def test_cython_order_book_creation():
    book = CythonOrderBook()

    assert book is not None


def test_cython_order_attributes_are_mutable():
    order = CythonOrder(
        1,
        100.0,
        50,
        True,
        1
    )

    order.quantity = 25
    order.price = 101.0

    assert order.quantity == 25
    assert order.price == 101.0
def test_cython_add_buy_order():
    book = CythonOrderBook()

    order = CythonOrder(
        1,
        100.0,
        50,
        True,
        1
    )

    book.add_order(order)

    assert len(book.buy_orders) == 1
    assert book.buy_orders[0].order_id == 1
    assert book.buy_orders[0].price == 100.0
    assert book.buy_orders[0].quantity == 50


def test_cython_add_sell_order():
    book = CythonOrderBook()

    order = CythonOrder(
        2,
        101.0,
        30,
        False,
        1
    )

    book.add_order(order)

    assert len(book.sell_orders) == 1
    assert book.sell_orders[0].order_id == 2
    assert book.sell_orders[0].price == 101.0
    assert book.sell_orders[0].quantity == 30
def test_cython_cancel_buy_order():
    book = CythonOrderBook()

    order = CythonOrder(
        101,
        100.0,
        50,
        True,
        1
    )

    book.add_order(order)

    result = book.cancel_order(101)

    assert result is True
    assert len(book.buy_orders) == 0


def test_cython_cancel_sell_order():
    book = CythonOrderBook()

    order = CythonOrder(
        102,
        101.0,
        30,
        False,
        1
    )

    book.add_order(order)

    result = book.cancel_order(102)

    assert result is True
    assert len(book.sell_orders) == 0


def test_cython_cancel_nonexistent_order():
    book = CythonOrderBook()

    result = book.cancel_order(999)

    assert result is False
def test_cython_full_match():
    book = CythonOrderBook()

    sell_order = CythonOrder(
        1,
        100.0,
        50,
        False,
        1
    )

    buy_order = CythonOrder(
        2,
        100.0,
        50,
        True,
        2
    )

    book.add_order(sell_order)

    trades = book.match_order(buy_order)

    assert len(trades) == 1

    assert trades[0]["buy_order_id"] == 2
    assert trades[0]["sell_order_id"] == 1
    assert trades[0]["price"] == 100.0
    assert trades[0]["quantity"] == 50

    assert buy_order.quantity == 0
    assert len(book.buy_orders) == 0
    assert len(book.sell_orders) == 0
def test_cython_partial_fill():
    book = CythonOrderBook()

    sell_order = CythonOrder(
        1,
        100.0,
        50,
        False,
        1
    )

    buy_order = CythonOrder(
        2,
        100.0,
        80,
        True,
        2
    )

    book.add_order(sell_order)

    trades = book.match_order(buy_order)

    assert len(trades) == 1

    assert trades[0]["buy_order_id"] == 2
    assert trades[0]["sell_order_id"] == 1
    assert trades[0]["price"] == 100.0
    assert trades[0]["quantity"] == 50

    assert buy_order.quantity == 30
    assert len(book.sell_orders) == 0

    assert len(book.buy_orders) == 1
    assert book.buy_orders[0].quantity == 30
def test_cython_multiple_price_level_matching():
    book = CythonOrderBook()

    sell1 = CythonOrder(
        1,
        100.0,
        50,
        False,
        1
    )

    sell2 = CythonOrder(
        2,
        101.0,
        30,
        False,
        2
    )

    sell3 = CythonOrder(
        3,
        102.0,
        40,
        False,
        3
    )

    book.add_order(sell1)
    book.add_order(sell2)
    book.add_order(sell3)

    buy_order = CythonOrder(
        4,
        101.0,
        70,
        True,
        4
    )

    trades = book.match_order(buy_order)

    assert len(trades) == 2

    assert trades[0]["sell_order_id"] == 1
    assert trades[0]["price"] == 100.0
    assert trades[0]["quantity"] == 50

    assert trades[1]["sell_order_id"] == 2
    assert trades[1]["price"] == 101.0
    assert trades[1]["quantity"] == 20

    assert buy_order.quantity == 0

    assert len(book.sell_orders) == 2

    assert book.sell_orders[0].order_id == 2
    assert book.sell_orders[0].quantity == 10

    assert book.sell_orders[1].order_id == 3
    assert book.sell_orders[1].quantity == 40
def test_cython_sell_matches_multiple_buy_levels():
    book = CythonOrderBook()

    buy1 = CythonOrder(
        1,
        101.0,
        30,
        True,
        1
    )

    buy2 = CythonOrder(
        2,
        100.0,
        50,
        True,
        2
    )

    buy3 = CythonOrder(
        3,
        99.0,
        40,
        True,
        3
    )

    book.add_order(buy1)
    book.add_order(buy2)
    book.add_order(buy3)

    sell_order = CythonOrder(
        4,
        100.0,
        70,
        False,
        4
    )

    trades = book.match_order(sell_order)

    assert len(trades) == 2

    assert trades[0]["buy_order_id"] == 1
    assert trades[0]["price"] == 101.0
    assert trades[0]["quantity"] == 30

    assert trades[1]["buy_order_id"] == 2
    assert trades[1]["price"] == 100.0
    assert trades[1]["quantity"] == 40

    assert sell_order.quantity == 0

    assert len(book.buy_orders) == 2

    assert book.buy_orders[0].order_id == 2
    assert book.buy_orders[0].quantity == 10

    assert book.buy_orders[1].order_id == 3
    assert book.buy_orders[1].quantity == 40
def test_cython_non_matching_buy_order():
    book = CythonOrderBook()

    sell_order = CythonOrder(
        1,
        105.0,
        50,
        False,
        1
    )

    buy_order = CythonOrder(
        2,
        100.0,
        30,
        True,
        2
    )

    book.add_order(sell_order)

    trades = book.match_order(buy_order)

    assert len(trades) == 0

    assert len(book.sell_orders) == 1
    assert book.sell_orders[0].order_id == 1
    assert book.sell_orders[0].quantity == 50

    assert len(book.buy_orders) == 1
    assert book.buy_orders[0].order_id == 2
    assert book.buy_orders[0].quantity == 30


def test_cython_non_matching_sell_order():
    book = CythonOrderBook()

    buy_order = CythonOrder(
        1,
        95.0,
        50,
        True,
        1
    )

    sell_order = CythonOrder(
        2,
        100.0,
        30,
        False,
        2
    )

    book.add_order(buy_order)

    trades = book.match_order(sell_order)

    assert len(trades) == 0

    assert len(book.buy_orders) == 1
    assert book.buy_orders[0].order_id == 1
    assert book.buy_orders[0].quantity == 50

    assert len(book.sell_orders) == 1
    assert book.sell_orders[0].order_id == 2
    assert book.sell_orders[0].quantity == 30