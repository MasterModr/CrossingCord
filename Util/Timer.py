import time, threading

def setInterval(interval, times = -1):
    # This will be the actual decorator,
    # with fixed interval and times parameter
    def outer_wrap(function):
        # This will be the function to be
        # called
        def wrap(*args, **kwargs):
            # This is another function to be executed
            # in a different thread to simulate setInterval
            def inner_wrap():
                i = 0
                while i != times:
                    time.sleep(interval)
                    function(*args, **kwargs)
                    i += 1
            threading.Timer(0, inner_wrap).start()
        return wrap
    return outer_wrap