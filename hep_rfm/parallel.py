'''
Tools and function to do parallelization of jobs.
'''

# Python
import multiprocessing as mp
from queue import Empty


__all__ = []


def log( logcall, string, lock=None ):
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

    def __init__( self ):
        '''
        Class to handle jobs on a parallelized environment.
        Build the class to handling a queue and a set of workers.
        '''
        super(JobHandler, self).__init__()

        self._queue   = mp.JoinableQueue()
        self._workers = []

    def add_worker( self, worker ):
        '''
        Add a new worker to this class.

        :param worker: worker to add.
        :type worker: Worker
        '''
        self._workers.append(worker)

    def get( self ):
        '''
        Get an object from the queue. This function does not block.
        '''
        return self._queue.get_nowait()

    def put( self, el ):
        '''
        Put an element in a process queue.

        :param el: object to add to the queue.
        :type el: serializable object
        '''
        self._queue.put(el)

    def task_done( self ):
        '''
        Set the task as done.
        '''
        self._queue.task_done()

    def process( self ):
        '''
        Wait until all jobs are completed and no elements are found in the \
        queue.
        '''
        for w in self._workers:
            w.start()
        self._queue.close()
        self._queue.join()


class Worker(object):

    def __init__( self, handler, func, args=(), kwargs={} ):
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

        self._process = mp.Process(target=self._execute, args=args, kwargs=kwargs)
        self._handler = handler

        self._handler.add_worker(self)

    def _execute( self, *args, **kwargs ):
        '''
        Parallelizable method to call the stored function using items
        from the queue of the handler.
        '''
        while True:

            try:
                obj = self._handler.get()
            except Empty:
                break

            self._func(obj, *args, **kwargs)

            self._handler.task_done()

    def start( self ):
        '''
        Start processing.
        '''
        self._process.start()
