from cython_engine.order_book import CythonOrder, CythonOrderBook


cdef class CythonMatchingEngine:

    cdef object book

    def __cinit__(self):
        self.book = CythonOrderBook()

    cpdef add_order(
        self,
        int order_id,
        double price,
        int quantity,
        bint is_buy,
        long long timestamp
    ):
        order = CythonOrder(
            order_id,
            price,
            quantity,
            is_buy,
            timestamp
        )

        self.book.add_order(order)

    cpdef cancel_order(self, int order_id):
        return self.book.cancel_order(order_id)

    cpdef match_order(
        self,
        int order_id,
        double price,
        int quantity,
        bint is_buy,
        long long timestamp
    ):
        order = CythonOrder(
            order_id,
            price,
            quantity,
            is_buy,
            timestamp
        )

        return self.book.match_order(order)

    cpdef get_buy_order_count(self):
        return len(self.book.buy_orders)

    cpdef get_sell_order_count(self):
        return len(self.book.sell_orders)