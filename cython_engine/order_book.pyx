def _sell_sort_key(order):
    return (order.price, order.timestamp)


def _buy_sort_key(order):
    return (-order.price, order.timestamp)


cdef class CythonOrder:

    cdef public int order_id
    cdef public double price
    cdef public int quantity
    cdef public bint is_buy
    cdef public long long timestamp

    def __cinit__(
        self,
        int order_id,
        double price,
        int quantity,
        bint is_buy,
        long long timestamp
    ):
        self.order_id = order_id
        self.price = price
        self.quantity = quantity
        self.is_buy = is_buy
        self.timestamp = timestamp


cdef class CythonOrderBook:

    cdef public list buy_orders
    cdef public list sell_orders

    def __cinit__(self):
        self.buy_orders = []
        self.sell_orders = []

    cpdef add_order(self, CythonOrder order):
        if order.is_buy:
            self.buy_orders.append(order)
        else:
            self.sell_orders.append(order)

    cpdef cancel_order(self, int order_id):
        for order in self.buy_orders:
            if order.order_id == order_id:
                self.buy_orders.remove(order)
                return True

        for order in self.sell_orders:
            if order.order_id == order_id:
                self.sell_orders.remove(order)
                return True

        return False

    cpdef match_order(self, CythonOrder incoming_order):
        trades = []

        if incoming_order.is_buy:

            opposite_orders = sorted(
                self.sell_orders,
                key=_sell_sort_key
            )

            for resting_order in opposite_orders:

                if incoming_order.price < resting_order.price:
                    break

                trade_quantity = min(
                    incoming_order.quantity,
                    resting_order.quantity
                )

                trades.append({
                    "buy_order_id": incoming_order.order_id,
                    "sell_order_id": resting_order.order_id,
                    "price": resting_order.price,
                    "quantity": trade_quantity
                })

                incoming_order.quantity -= trade_quantity
                resting_order.quantity -= trade_quantity

                if resting_order.quantity == 0:
                    self.sell_orders.remove(resting_order)

                if incoming_order.quantity == 0:
                    break

            if incoming_order.quantity > 0:
                self.add_order(incoming_order)

        else:

            opposite_orders = sorted(
                self.buy_orders,
                key=_buy_sort_key
            )

            for resting_order in opposite_orders:

                if incoming_order.price > resting_order.price:
                    break

                trade_quantity = min(
                    incoming_order.quantity,
                    resting_order.quantity
                )

                trades.append({
                    "buy_order_id": resting_order.order_id,
                    "sell_order_id": incoming_order.order_id,
                    "price": resting_order.price,
                    "quantity": trade_quantity
                })

                incoming_order.quantity -= trade_quantity
                resting_order.quantity -= trade_quantity

                if resting_order.quantity == 0:
                    self.buy_orders.remove(resting_order)

                if incoming_order.quantity == 0:
                    break

            if incoming_order.quantity > 0:
                self.add_order(incoming_order)

        return trades