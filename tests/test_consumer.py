import os

from consumer.consumer import OrderConsumer
from ipc import Order, BUY, SELL, RingBuffer


def test_consumer_processes_matching_orders(tmp_path):
    ipc_file = str(
        tmp_path / "test_chronosmatch.ipc"
    )

    producer_buffer = RingBuffer(
        path=ipc_file,
        capacity=100,
    )

    producer_buffer.create()

    producer_buffer.write(
        Order(
            order_id=1,
            price=100.0,
            quantity=50,
            side=SELL,
            timestamp_ns=1,
        )
    )

    producer_buffer.write(
        Order(
            order_id=2,
            price=100.0,
            quantity=50,
            side=BUY,
            timestamp_ns=2,
        )
    )

    consumer = OrderConsumer(
        ipc_file=ipc_file,
        buffer_capacity=100,
    )

    try:
        consumer.connect()

        first_order = consumer.ring_buffer.read()
        assert first_order is not None

        first_trades = consumer.engine.match_order(
            first_order.order_id,
            first_order.price,
            first_order.quantity,
            first_order.side == BUY,
            first_order.timestamp_ns,
        )

        assert first_trades == []

        second_order = consumer.ring_buffer.read()
        assert second_order is not None

        second_trades = consumer.engine.match_order(
            second_order.order_id,
            second_order.price,
            second_order.quantity,
            second_order.side == BUY,
            second_order.timestamp_ns,
        )

        assert len(second_trades) == 1
        assert second_trades[0]["buy_order_id"] == 2
        assert second_trades[0]["sell_order_id"] == 1
        assert second_trades[0]["price"] == 100.0
        assert second_trades[0]["quantity"] == 50

    finally:
        consumer.close()
        producer_buffer.close()

        if os.path.exists(ipc_file):
            os.remove(ipc_file)