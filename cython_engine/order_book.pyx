import time
from libc.stdlib cimport malloc, realloc, free


cdef struct OrderData:
    int order_id
    double price
    int quantity
    bint is_buy
    long long timestamp


cdef struct TradeData:
    int buy_order_id
    int sell_order_id
    double price
    int quantity


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

    cdef OrderData* buy_data
    cdef OrderData* sell_data

    cdef int buy_size
    cdef int sell_size

    cdef int buy_capacity
    cdef int sell_capacity

    cdef public long long last_match_latency_ns

    def __cinit__(self):

        self.buy_orders = []
        self.sell_orders = []

        self.buy_data = NULL
        self.sell_data = NULL

        self.buy_size = 0
        self.sell_size = 0

        self.buy_capacity = 0
        self.sell_capacity = 0

        self.last_match_latency_ns = 0

    def __dealloc__(self):

        if self.buy_data != NULL:
            free(self.buy_data)

        if self.sell_data != NULL:
            free(self.sell_data)

    # ============================================================
    # C-LEVEL CAPACITY MANAGEMENT
    # ============================================================

    cdef void _ensure_buy_capacity(self):

        cdef OrderData* new_data
        cdef int new_capacity

        if self.buy_size < self.buy_capacity:
            return

        if self.buy_capacity == 0:
            new_capacity = 16
        else:
            new_capacity = self.buy_capacity * 2

        new_data = <OrderData*>realloc(
            self.buy_data,
            new_capacity * sizeof(OrderData)
        )

        if new_data == NULL:
            raise MemoryError(
                "Unable to allocate buy order storage"
            )

        self.buy_data = new_data
        self.buy_capacity = new_capacity

    cdef void _ensure_sell_capacity(self):

        cdef OrderData* new_data
        cdef int new_capacity

        if self.sell_size < self.sell_capacity:
            return

        if self.sell_capacity == 0:
            new_capacity = 16
        else:
            new_capacity = self.sell_capacity * 2

        new_data = <OrderData*>realloc(
            self.sell_data,
            new_capacity * sizeof(OrderData)
        )

        if new_data == NULL:
            raise MemoryError(
                "Unable to allocate sell order storage"
            )

        self.sell_data = new_data
        self.sell_capacity = new_capacity

    # ============================================================
    # C-LEVEL ORDER INSERTION
    # ============================================================

    cdef void _insert_buy_data(
        self,
        OrderData order
    ):

        cdef int position
        cdef int i

        self._ensure_buy_capacity()

        position = self.buy_size

        while position > 0:

            if (
                self.buy_data[position - 1].price > order.price
            ):
                break

            if (
                self.buy_data[position - 1].price == order.price
                and
                self.buy_data[position - 1].timestamp
                <= order.timestamp
            ):
                break

            position -= 1

        for i in range(self.buy_size, position, -1):
            self.buy_data[i] = self.buy_data[i - 1]

        self.buy_data[position] = order
        self.buy_size += 1

    cdef void _insert_sell_data(
        self,
        OrderData order
    ):

        cdef int position
        cdef int i

        self._ensure_sell_capacity()

        position = self.sell_size

        while position > 0:

            if (
                self.sell_data[position - 1].price < order.price
            ):
                break

            if (
                self.sell_data[position - 1].price == order.price
                and
                self.sell_data[position - 1].timestamp
                <= order.timestamp
            ):
                break

            position -= 1

        for i in range(self.sell_size, position, -1):
            self.sell_data[i] = self.sell_data[i - 1]

        self.sell_data[position] = order
        self.sell_size += 1

    # ============================================================
    # C-LEVEL REMOVAL
    # ============================================================

    cdef void _remove_buy_data(
        self,
        int index
    ):

        cdef int i

        for i in range(index, self.buy_size - 1):
            self.buy_data[i] = self.buy_data[i + 1]

        self.buy_size -= 1

    cdef void _remove_sell_data(
        self,
        int index
    ):

        cdef int i

        for i in range(index, self.sell_size - 1):
            self.sell_data[i] = self.sell_data[i + 1]

        self.sell_size -= 1

    # ============================================================
    # PUBLIC ADD ORDER
    # ============================================================

    cpdef add_order(
        self,
        CythonOrder order
    ):

        cdef OrderData data

        data.order_id = order.order_id
        data.price = order.price
        data.quantity = order.quantity
        data.is_buy = order.is_buy
        data.timestamp = order.timestamp

        if order.is_buy:

            self._insert_buy_data(data)
            self.buy_orders.append(order)

        else:

            self._insert_sell_data(data)
            self.sell_orders.append(order)

    # ============================================================
    # PUBLIC CANCEL
    # ============================================================

    cpdef cancel_order(
        self,
        int order_id
    ):

        cdef int i
        cdef CythonOrder order

        for i in range(self.buy_size):

            if self.buy_data[i].order_id == order_id:

                self._remove_buy_data(i)

                for order in self.buy_orders:

                    if order.order_id == order_id:
                        self.buy_orders.remove(order)
                        break

                return True

        for i in range(self.sell_size):

            if self.sell_data[i].order_id == order_id:

                self._remove_sell_data(i)

                for order in self.sell_orders:

                    if order.order_id == order_id:
                        self.sell_orders.remove(order)
                        break

                return True

        return False

    # ============================================================
    # PYTHON BOOK SYNCHRONIZATION
    #
    # IMPORTANT:
    # This function is called AFTER the matching loop.
    # It is NOT part of the C-level hot path.
    # ============================================================

    cdef void _sync_python_book(self):

        cdef int i
        cdef int j
        cdef bint found
        cdef CythonOrder order

        cdef list new_buy_orders
        cdef list new_sell_orders

        new_buy_orders = []

        for order in self.buy_orders:

            found = False

            for i in range(self.buy_size):

                if (
                    self.buy_data[i].order_id
                    == order.order_id
                ):

                    order.quantity = (
                        self.buy_data[i].quantity
                    )

                    found = True
                    break

            if found:
                new_buy_orders.append(order)

        new_sell_orders = []

        for order in self.sell_orders:

            found = False

            for j in range(self.sell_size):

                if (
                    self.sell_data[j].order_id
                    == order.order_id
                ):

                    order.quantity = (
                        self.sell_data[j].quantity
                    )

                    found = True
                    break

            if found:
                new_sell_orders.append(order)

        self.buy_orders = new_buy_orders
        self.sell_orders = new_sell_orders

    # ============================================================
    # MATCHING ENGINE
    # ============================================================

    cpdef match_order(
        self,
        CythonOrder incoming_order
    ):

        cdef OrderData incoming
        cdef OrderData resting

        cdef TradeData* trade_data
        cdef TradeData* new_trade_data

        cdef int trade_count
        cdef int trade_capacity
        cdef int trade_quantity
        cdef int i

        cdef long long match_start_ns
        cdef long long match_end_ns

        cdef bint is_buy

        cdef list trades

        incoming.order_id = incoming_order.order_id
        incoming.price = incoming_order.price
        incoming.quantity = incoming_order.quantity
        incoming.is_buy = incoming_order.is_buy
        incoming.timestamp = incoming_order.timestamp

        trade_data = NULL
        trade_count = 0
        trade_capacity = 0

        is_buy = incoming.is_buy

        # ========================================================
        # START ENGINE LATENCY MEASUREMENT
        # ========================================================

        match_start_ns = time.perf_counter_ns()

        # ========================================================
        # BUY MATCHING
        #
        # buy_data is sorted:
        # highest price → lowest price
        # same price → earliest timestamp
        #
        # Therefore index 0 is always the best BUY.
        # ========================================================

        if is_buy:

            while (
                incoming.quantity > 0
                and self.sell_size > 0
            ):

                resting = self.sell_data[0]

                if incoming.price < resting.price:
                    break

                if incoming.quantity < resting.quantity:
                    trade_quantity = incoming.quantity
                else:
                    trade_quantity = resting.quantity

                # Grow C-level trade storage.
                if trade_count >= trade_capacity:

                    if trade_capacity == 0:
                        trade_capacity = 8
                    else:
                        trade_capacity = trade_capacity * 2

                    new_trade_data = <TradeData*>realloc(
                        trade_data,
                        trade_capacity * sizeof(TradeData)
                    )

                    if new_trade_data == NULL:

                        if trade_data != NULL:
                            free(trade_data)

                        raise MemoryError(
                            "Unable to allocate trade storage"
                        )

                    trade_data = new_trade_data

                # Store trade entirely in C memory.
                trade_data[trade_count].buy_order_id = (
                    incoming.order_id
                )

                trade_data[trade_count].sell_order_id = (
                    resting.order_id
                )

                trade_data[trade_count].price = (
                    resting.price
                )

                trade_data[trade_count].quantity = (
                    trade_quantity
                )

                trade_count += 1

                incoming.quantity -= trade_quantity

                self.sell_data[0].quantity -= (
                    trade_quantity
                )

                if self.sell_data[0].quantity == 0:

                    self._remove_sell_data(0)

        # ========================================================
        # SELL MATCHING
        #
        # buy_data is sorted:
        # highest price → lowest price
        # same price → earliest timestamp
        #
        # Therefore index 0 is always the best BUY.
        # ========================================================

        else:

            while (
                incoming.quantity > 0
                and self.buy_size > 0
            ):

                resting = self.buy_data[0]

                if incoming.price > resting.price:
                    break

                if incoming.quantity < resting.quantity:
                    trade_quantity = incoming.quantity
                else:
                    trade_quantity = resting.quantity

                # Grow C-level trade storage.
                if trade_count >= trade_capacity:

                    if trade_capacity == 0:
                        trade_capacity = 8
                    else:
                        trade_capacity = trade_capacity * 2

                    new_trade_data = <TradeData*>realloc(
                        trade_data,
                        trade_capacity * sizeof(TradeData)
                    )

                    if new_trade_data == NULL:

                        if trade_data != NULL:
                            free(trade_data)

                        raise MemoryError(
                            "Unable to allocate trade storage"
                        )

                    trade_data = new_trade_data

                # Store trade entirely in C memory.
                trade_data[trade_count].buy_order_id = (
                    resting.order_id
                )

                trade_data[trade_count].sell_order_id = (
                    incoming.order_id
                )

                trade_data[trade_count].price = (
                    resting.price
                )

                trade_data[trade_count].quantity = (
                    trade_quantity
                )

                trade_count += 1

                incoming.quantity -= trade_quantity

                self.buy_data[0].quantity -= (
                    trade_quantity
                )

                if self.buy_data[0].quantity == 0:

                    self._remove_buy_data(0)

        # ========================================================
        # END C-LEVEL MATCHING
        #
        # This timestamp is captured before Python synchronization
        # and Python trade dictionary creation.
        # ========================================================

        match_end_ns = time.perf_counter_ns()

        self.last_match_latency_ns = (
            match_end_ns - match_start_ns
        )

        # Update incoming Python object's remaining quantity.
        incoming_order.quantity = incoming.quantity

        # ========================================================
        # ADD REMAINING INCOMING ORDER TO C-LEVEL BOOK
        # ========================================================

        if incoming.quantity > 0:

            if incoming.is_buy:
                self._insert_buy_data(incoming)
            else:
                self._insert_sell_data(incoming)

        # ========================================================
        # PYTHON BOOK SYNCHRONIZATION
        #
        # OUTSIDE THE MATCHING HOT PATH.
        # ========================================================

        self._sync_python_book()

        if incoming.quantity > 0:

            if incoming.is_buy:
                self.buy_orders.append(incoming_order)
            else:
                self.sell_orders.append(incoming_order)

        # ========================================================
        # CONVERT C-LEVEL TRADES TO PYTHON RESULTS
        #
        # OUTSIDE THE MATCHING HOT PATH.
        # ========================================================

        trades = []

        for i in range(trade_count):

            trades.append({
                "buy_order_id":
                    trade_data[i].buy_order_id,

                "sell_order_id":
                    trade_data[i].sell_order_id,

                "price":
                    trade_data[i].price,

                "quantity":
                    trade_data[i].quantity
            })

        if trade_data != NULL:
            free(trade_data)

        return trades