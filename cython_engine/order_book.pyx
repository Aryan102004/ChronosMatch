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

    def __cinit__(self):
        self.buy_orders = []
        self.sell_orders = []