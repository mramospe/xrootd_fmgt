'''
Tools and function to do parallelization of jobs.
'''

# Python
import logging, os, sys
import multiprocessing as mp


__all__ = []


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

    def wait( self ):
        '''
        Wait until all jobs are completed and no elements are found in the \
        queue.
        '''
        self._queue.close()
        self._queue.join()

        for w in self._workers:
            w.terminate()


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
        while True:

            obj = self._handler.queue().get(block=True, timeout=None)

            self.func(obj, *args, **kwargs)

            self._handler.queue().task_done()

    def terminate( self ):
        '''
        Terminate the owned process. No check is done to see whether the process
        was running or not.
        '''
        self._process.terminate()
