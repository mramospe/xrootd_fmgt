'''
Tools and function to do parallelization of jobs.
'''

# Python
import logging, os, sys
import multiprocessing as mp


__all__ = []


class JobHandler:
    '''
    Class to handle jobs on a parallelized environment.
    '''
    def __init__( self ):
        '''
        Build the class to handling a queue and a set of workers.
        '''
        self.queue   = mp.JoinableQueue()
        self.workers = []

    def add_worker( self, worker ):
        '''
        Add a new worker to this class.

        :param worker: worker to add.
        :type worker: Worker
        '''
        self.workers.append(worker)

    def wait( self ):
        '''
        Wait until all jobs are completed and no elements are found in the \
        queue.
        '''
        self.queue.close()
        self.queue.join()

        for w in self.workers:
            w.terminate()


class Worker:
    '''
    Class to build a process on a parallelized environment.
    '''

    def __init__( self, handler, args=(), kwargs={} ):
        '''
        Build a worker providing the job handler. The worker is automatically
        registered in the handler via the :meth:`JobHandler.add_worker` method.

        :param handler: instance to handle workers.
        :type handler: JobHandler
        :param args: extra arguments to :meth:`Worker.execute`.
        :type args: tuple
        :param kwargs: extra keyword-arguments to :meth:`Worker.execute`.
        :type kwargs: dict
        '''
        self._process = mp.Process(target=self._execute, args=args, kwargs=kwargs)
        self._handler = handler

        self._handler.add_worker(self)

        self._process.start()

    def _execute( self, *args, **kwargs ):
        '''
        Base method to call on a parallelized environment, which calls the
        :meth:`Worker.execute` method after taking an element from the queue.

        :param args: extra arguments to :meth:`Worker.execute`.
        :type args: tuple
        :param kwargs: extra keyword-arguments to :meth:`Worker.execute`.
        :type kwargs: dict
        '''
        while True:

            obj = self._handler.queue.get(block=True, timeout=None)

            self.execute(obj, *args, **kwargs)

            self._handler.queue.task_done()

    def execute( self, obj, *args, **kwargs ):
        '''
        Main method to be called by the process. It must be overriden by
        any inheriting class.

        :param obj: any object stored in the queue.
        :type obj: object
        '''
        raise NotImplementedError('Attempt to call abstract class method')

    def terminate( self ):
        '''
        Terminate the owned process. No check is done to see whether the process
        was running or not.
        '''
        self._process.terminate()


class FuncWorker(Worker):
    '''
    Worker which executes a function when the method :meth:`FuncWorker.execute`
    is called.
    '''
    def __init__( self, handler, func, args=(), kwargs={} ):
        '''
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

        Worker.__init__(self, handler, args, kwargs)

    def execute( self, obj, *args, **kwargs ):
        '''
        Execute the function using the given object as an argument.

        :param obj: any object stored in the queue.
        :type obj: object
        '''
        self.func(obj, *args, **kwargs)
