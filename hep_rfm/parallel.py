'''
Tools and function to do parallelization of jobs.
'''

# Python
import multiprocessing as mp


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


class JobHandler:

    def __init__( self, inputs, nproc=1 ):
        '''
        Class to handle jobs on a parallelized environment.
        Build the class to handling a queue and a set of workers.

        :param inputs: inputs to the queue.
        :type inputs: list
        :param nproc: number of processes to generate. In case this number is \
        greater than the number of inputs, it will be set to the smallest \
        value of the two.
        :type nproc: int
        '''
        self._queue   = mp.JoinableQueue()
        self._workers = []
        self._termsig = mp.Event()

        for i in inputs:
            self._queue.put(i)

        # Prevent from creating extra processes which might end up
        # as zombies
        self.nproc = min(nproc, len(inputs))

    def add_worker( self, worker ):
        '''
        Add a new worker to this class.

        :param worker: worker to add.
        :type worker: Worker
        '''
        self._workers.append(worker)

    def queue( self ):
        '''
        Get the queue used by this class.

        :returns: queue used by this class.
        :rtype: multiprocessing.queues.JoinableQueue
        '''
        return self._queue

    def task_done( self ):
        '''
        Set the task as done.
        '''
        self._queue.task_done()
        if self._queue.empty():
            self._termsig.set()

    def wait( self ):
        '''
        Wait until all jobs are completed and no elements are found in the \
        queue.
        '''
        self._queue.close()
        self._queue.join()


class Worker:

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
        self.func = func

        self._process = mp.Process(target=self._execute, args=args, kwargs=kwargs)
        self._handler = handler

        self._handler.add_worker(self)

        self._process.start()

    def _execute( self, *args, **kwargs ):
        '''
        Parallelizable method to call the stored function using items
        from the queue of the handler.
        '''
        while not self._handler._termsig.is_set():

            obj = self._handler.queue().get(block=True, timeout=None)

            self.func(obj, *args, **kwargs)

            self._handler.task_done()
