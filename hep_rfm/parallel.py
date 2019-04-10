'''
Tools and function to do parallelization of jobs.
'''

# Python
import logging
import multiprocessing as mp
from queue import Empty


__all__ = []


def log(logcall, string, lock=None):
    '''
    Report an information/warning/error/debug... message with a logger instance
    but taken into account a lock if given.

    :param logcall: call of the logger to perform.
    :type logcall: method
    :param string: string to pass by argument to the call.
    :type string: str
    :param lock: possible lock instance.
    :type lock: multiprocessing.Lock
    '''
    if lock:
        lock.acquire()
        logcall(string)
        lock.release()
    else:
        logcall(string)


class JobHandler(object):

    def __init__(self):
        '''
        Class to handle jobs on a parallelized environment.
        Build the class to handling a queue and a set of workers.
        '''
        super(JobHandler, self).__init__()

        self._queue = mp.JoinableQueue()
        self._workers = []
        self._failed  = mp.Value('i', 0)

    def add_worker(self, worker):
        '''
        Add a new worker to this class.

        :param worker: worker to add.
        :type worker: Worker
        '''
        self._workers.append(worker)

    def get(self):
        '''
        Get an object from the queue. This function does not block.
        '''
        return self._queue.get_nowait()

    def notify_failed(self):
        '''
        Notify the handler that a job has failed.
        '''
        with self._failed.get_lock():
            self._failed.value += 1

    def put(self, el):
        '''
        Put an element in a process queue.

        :param el: object to add to the queue.
        :type el: serializable object
        '''
        self._queue.put(el)

    def task_done(self):
        '''
        Set the task as done.
        '''
        self._queue.task_done()

    def process(self):
        '''
        Wait until all jobs are completed and no elements are found in the
        queue.

        :raises RuntimeError: if any of the workers fails on execution.
        '''
        self._failed.value = 0
        for w in self._workers:
            w.start()
        self._queue.close()
        self._queue.join()

        if self._failed.value != 0:
            raise RuntimeError(
                '{} jobs processed with errors'.format(self._failed.value))


class Registry(object):

    def __init__(self):
        '''
        Define a registry of objects, where the operation of setting the objects
        is thread-safe.
        '''
        super(Registry, self).__init__()

        self._lock = mp.Lock()
        self._registry = {}

    def __contains__(self, key):
        '''
        Check whether the given key is registered.

        :param key: key object.
        :type key: hashable object.
        :returns: whether the key is registered.
        :rtype: bool
        '''
        return key in self._registry

    def __getitem__(self, key):
        '''
        Get an item from the registry.

        :param key: key object.
        :type key: hashable object
        :returns: value object.
        :rtype: object
        '''
        return self._registry[key]

    def __setitem__(self, key, value):
        '''
        Set an item, locking the access.

        :param key: key object.
        :type key: hashable object
        :param value: value object.
        :type value: object
        '''
        with self._lock:
            self._registry[key] = value


class Worker(object):

    def __init__(self, handler, func, args=(), kwargs={}):
        '''
        Worker which executes a function when the method :meth:`Worker._execute`
        is called.
        Build the class using the job handler and an input function to be
        called on execution.

        :param handler: instance to handle workers.
        :type handler: JobHandler
        :param func: function to call.
        :type func: function
        :param args: extra arguments to multiprocessing.Process.
        :type args: tuple
        :param kwargs: extra keyword-arguments to multiprocessing.Process \
        (excepting "target", which is automatically asigned).
        :type kwargs: dict
        '''
        super(Worker, self).__init__()

        self._func = func

        self._process = mp.Process(
            target=self._execute, args=args, kwargs=kwargs)
        self._handler = handler

        self._handler.add_worker(self)

    def _execute(self, *args, **kwargs):
        '''
        Parallelizable method to call the stored function using items
        from the queue of the handler.
        '''
        while True:

            try:
                obj = self._handler.get()
            except Empty:
                break

            try:
                self._func(obj, *args, **kwargs)

            except Exception as e:

                logging.getLogger(__name__).error(str(e))

                self._handler.notify_failed()

            finally:
                self._handler.task_done()

    def start(self):
        '''
        Start processing.
        Any error raised on execution will be displayed using the related
        logger object, and handled by the :class:`JobHandler`.
        '''
        self._process.start()
