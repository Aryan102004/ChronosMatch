from cython_engine.python_order_book import Order, OrderBook


def test_add_buy_order():
    book = OrderBook()

    order = Order(
        order_id=1,
        price=100.0,
        quantity=50,
        side="BUY",
        timestamp=1
    )

    book.add_order(order)

    assert len(book.buy_orders) == 1
    assert book.buy_orders[0].order_id == 1
    assert book.buy_orders[0].price == 100.0
    assert book.buy_orders[0].quantity == 50


def test_add_sell_order():
    book = OrderBook()

    order = Order(
        order_id=2,
        price=101.0,
        quantity=30,
        side="SELL",
        timestamp=2
    )

    book.add_order(order)

    assert len(book.sell_orders) == 1
    assert book.sell_orders[0].order_id == 2
    assert book.sell_orders[0].price == 101.0
    assert book.sell_orders[0].quantity == 30


def test_order_is_stored_by_id():
    book = OrderBook()

    order = Order(
        order_id=100,
        price=99.5,
        quantity=25,
        side="BUY",
        timestamp=1
    )

    book.add_order(order)

    assert 100 in book.orders
    assert book.orders[100] is order


def test_buy_price_priority():
    book = OrderBook()

    order1 = Order(
        order_id=1,
        price=100.0,
        quantity=50,
        side="BUY",
        timestamp=1
    )

    order2 = Order(
        order_id=2,
        price=101.0,
        quantity=50,
        side="BUY",
        timestamp=2
    )

    book.add_order(order1)
    book.add_order(order2)

    sorted_buys = sorted(
        book.buy_orders,
        key=lambda x: (-x.price, x.timestamp)
    )

    assert sorted_buys[0].order_id == 2
    assert sorted_buys[1].order_id == 1


def test_buy_time_priority():
    book = OrderBook()

    order1 = Order(
        order_id=1,
        price=100.0,
        quantity=50,
        side="BUY",
        timestamp=1
    )

    order2 = Order(
        order_id=2,
        price=100.0,
        quantity=50,
        side="BUY",
        timestamp=2
    )

    book.add_order(order1)
    book.add_order(order2)

    sorted_buys = sorted(
        book.buy_orders,
        key=lambda x: (-x.price, x.timestamp)
    )

    assert sorted_buys[0].order_id == 1
    assert sorted_buys[1].order_id == 2


def test_full_match():
    book = OrderBook()

    sell_order = Order(
        order_id=1,
        price=100.0,
        quantity=50,
        side="SELL",
        timestamp=1
    )

    buy_order = Order(
        order_id=2,
        price=100.0,
        quantity=50,
        side="BUY",
        timestamp=2
    )

    book.add_order(sell_order)

    trades = book.match_order(buy_order)

    assert len(trades) == 1
    assert trades[0]["buy_order_id"] == 2
    assert trades[0]["sell_order_id"] == 1
    assert trades[0]["price"] == 100.0
    assert trades[0]["quantity"] == 50

    assert len(book.buy_orders) == 0
    assert len(book.sell_orders) == 0


def test_partial_fill_incoming_order():
    book = OrderBook()

    sell_order = Order(
        order_id=1,
        price=100.0,
        quantity=50,
        side="SELL",
        timestamp=1
    )

    buy_order = Order(
        order_id=2,
        price=100.0,
        quantity=80,
        side="BUY",
        timestamp=2
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


def test_partial_fill_resting_order():
    book = OrderBook()

    sell_order = Order(
        order_id=1,
        price=100.0,
        quantity=80,
        side="SELL",
        timestamp=1
    )

    buy_order = Order(
        order_id=2,
        price=100.0,
        quantity=50,
        side="BUY",
        timestamp=2
    )

    book.add_order(sell_order)

    trades = book.match_order(buy_order)

    assert len(trades) == 1

    assert trades[0]["buy_order_id"] == 2
    assert trades[0]["sell_order_id"] == 1
    assert trades[0]["price"] == 100.0
    assert trades[0]["quantity"] == 50

    assert buy_order.quantity == 0
    assert sell_order.quantity == 30

    assert len(book.buy_orders) == 0
    assert len(book.sell_orders) == 1
    assert book.sell_orders[0].quantity == 30

def test_multiple_price_level_matching():
     book = OrderBook()

     sell1 = Order(
        order_id=1,
        price=100.0,
        quantity=50,
        side="SELL",
        timestamp=1
    )

     sell2 = Order(
        order_id=2,
        price=101.0,
        quantity=30,
        side="SELL",
        timestamp=2
    )

     sell3 = Order(
        order_id=3,
        price=102.0,
        quantity=40,
        side="SELL",
        timestamp=3
    )

     book.add_order(sell1)
     book.add_order(sell2)
     book.add_order(sell3)

     buy_order = Order(
        order_id=4,
        price=101.0,
        quantity=70,
        side="BUY",
        timestamp=4
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
def test_sell_matches_multiple_buy_levels():
    book = OrderBook()

    buy1 = Order(
        order_id=1,
        price=101.0,
        quantity=30,
        side="BUY",
        timestamp=1
    )

    buy2 = Order(
        order_id=2,
        price=100.0,
        quantity=50,
        side="BUY",
        timestamp=2
    )

    buy3 = Order(
        order_id=3,
        price=99.0,
        quantity=40,
        side="BUY",
        timestamp=3
    )

    book.add_order(buy1)
    book.add_order(buy2)
    book.add_order(buy3)

    sell_order = Order(
        order_id=4,
        price=100.0,
        quantity=70,
        side="SELL",
        timestamp=4
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
def test_cancel_buy_order():
    book = OrderBook()

    order = Order(
        order_id=101,
        price=100.0,
        quantity=50,
        side="BUY",
        timestamp=1
    )

    book.add_order(order)

    result = book.cancel_order(101)

    assert result is True
    assert len(book.buy_orders) == 0
    assert 101 not in book.orders


def test_cancel_sell_order():
    book = OrderBook()

    order = Order(
        order_id=102,
        price=101.0,
        quantity=30,
        side="SELL",
        timestamp=1
    )

    book.add_order(order)

    result = book.cancel_order(102)

    assert result is True
    assert len(book.sell_orders) == 0
    assert 102 not in book.orders


def test_cancel_nonexistent_order():
    book = OrderBook()

    result = book.cancel_order(999)

    assert result is False

def test_non_matching_buy_order():
    book = OrderBook()

    sell_order = Order(
        order_id=1,
        price=105.0,
        quantity=50,
        side="SELL",
        timestamp=1
    )

    buy_order = Order(
        order_id=2,
        price=100.0,
        quantity=30,
        side="BUY",
        timestamp=2
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


def test_non_matching_sell_order():
    book = OrderBook()

    buy_order = Order(
        order_id=1,
        price=95.0,
        quantity=50,
        side="BUY",
        timestamp=1
    )

    sell_order = Order(
        order_id=2,
        price=100.0,
        quantity=30,
        side="SELL",
        timestamp=2
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