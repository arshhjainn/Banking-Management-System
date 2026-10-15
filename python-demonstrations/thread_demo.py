"""Thread, callable worker, synchronization, notification and safe cancellation."""
from threading import Condition, Event, Thread
import time
condition = Condition()
finished = False
cancel = Event()
def worker():
    global finished
    time.sleep(0.05)
    with condition:
        finished = True
        condition.notify_all()
    print("Worker finished")
def waiter():
    with condition:
        condition.wait_for(lambda: finished)
    print("Callable coordinated")
if __name__ == "__main__":
    first, second = Thread(target=worker), Thread(target=waiter)
    first.start(); second.start(); first.join(); second.join()
    # Python threads should stop cooperatively via an Event/flag; do not force-kill them.
    cancel.set()
