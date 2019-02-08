# ../avsd/core/database/thread.py

# ============================================================================
# >> IMPORTS
# ============================================================================
# Python Imports
#   Queue
# from queue import PriorityQueue
from queue import Queue
#   Sys
from sys import exc_info
#   Threading
from threading import Thread
#   Time
from time import sleep

# Source.Python Imports
#   Hooks
from hooks.exceptions import except_hooks
#   Listeners
from listeners.tick import Repeat


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
# _queue = PriorityQueue()
_queue = Queue()
_output = Queue()


# =============================================================================
# >> CLASSES
# =============================================================================
class _Result(object):
    def __init__(self, query=None, data=None, args=None, exception=None):
        self._query = query
        self._data = data
        self._args = args
        self._exception = exception
        self._lastrowid = None

        self._curindex = 0

    def __getitem__(self, name):
        return self._args[name]

    def fetchone(self):
        if len(self._data) <= self._curindex:
            return None

        data = self._data[self._curindex]
        self._curindex += 1

        return data

    def fetchall(self):
        data = self._data[self._curindex:]
        self._curindex = len(self._data)

        return data

    @property
    def query(self):
        return self._query

    @property
    def exception(self):
        return self._exception

    @property
    def lastrowid(self):
        return self._lastrowid


class _Thread(Thread):
    def run(self):
        self.connect()

        while True:
            query, arguments, callback, many, keywords = _queue.get()  # [1:]

            # if query is None and callback is None:
            #     break

            if query is None:
                if callback is None:
                    break

                result = _Result(args=keywords)

                _output.put((callback, result))

                if _queue.empty():
                    if self.con is not None and self.cur is not None:
                        self.close()

                continue

            if self.con is None or self.cur is None:
                self.connect()

            result = _Result(args=keywords, query=query)

            try:
                if many:
                    self.cur.executemany(query, arguments)
                else:
                    self.cur.execute(query, arguments)
            except:
                result._exception = exc_info()
            else:
                result._lastrowid = self.cur.lastrowid

            if callback is not None:
                result._data = self.cur.fetchall()

            if not (result.exception is None and callback is None):
                _output.put((callback, result))

            if _queue.empty():
                self.close()

            # self._execute(query, arguments, callback, many, keywords)

        if self.con is not None and self.cur is not None:
            self.close()

        _output.put((True, True))

    def _tick(self):
        for _ in range(16):
            if _output.empty():
                break

            callback, result = _output.get_nowait()

            if callback is True and result is True:
                _repeat.stop()
            else:
                if callback is not None:
                    try:
                        callback(result)
                    except:
                        except_hooks.print_exception()

                if result.exception:
                    print(result.query)
                    except_hooks.print_exception(*result.exception)

    # def _execute(self, query, arguments, callback, many, keywords):
    #     if query is None:
    #         if callback is not None:
    #             result = _Result(args=keywords)

    #             _output.put((callback, result))

    #         if _queue.empty():
    #             if self.con is not None and self.cur is not None:
    #                 self.close()

    #         return

    #     if self.con is None or self.cur is None:
    #         self.connect()

    #     result = _Result(args=keywords, query=query)

    #     try:
    #         if many:
    #             self.cur.executemany(query, arguments)
    #         else:
    #             self.cur.execute(query, arguments)
    #     except:
    #         result._exception = exc_info()
    #     else:
    #         result._lastrowid = self.cur.lastrowid

    #     if callback is not None:
    #         result._data = self.cur.fetchall()

    #     if not (result.exception is None and callback is None):
    #         _output.put((callback, result))

    #     if _queue.empty():
    #         self.close()

    def connect(self):
        if not hasattr(self, 'connector'):
            self.connector = _queue.get()  # [-1]

        while True:
            try:
                self.con = self.connector()
                self.cur = self.con.cursor()
            except:
                result = _Result(exception=exc_info())

                _output.put((None, result))

                sleep(30)
            else:
                break

    def close(self):
        self.con.commit()

        self.cur.close()
        self.con.close()

        self.cur = None
        self.con = None
_thread = _Thread()
# _thread.start()


class Repeat2(Repeat):
    def _unload_instance(self):
        pass  # I need to be sure the repeat does NOT stop at unload
_repeat = Repeat2(_thread._tick)
# _repeat.start(0.1)
