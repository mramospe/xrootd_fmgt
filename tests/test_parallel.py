'''
Test functions for the "parallel" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']

import hep_rfm
import multiprocessing as mp


def test_parallelization():
    '''
    Test the parallelization classes.
    '''
    jh = hep_rfm.parallel.JobHandler()

    def _func(i):
        pass

    for i in range(10):

        jh.put(i)

        hep_rfm.parallel.Worker(jh, _func)

    jh.process()


def test_parallelization_with_queues():
    '''
    Test the parallelization classes using externale queues.
    '''
    jh = hep_rfm.parallel.JobHandler()

    def _func(i, queue, extra):
        queue.put(i*extra)

    queue = mp.Queue()

    n = 4
    e = 2

    for i in range(n):

        jh.put(i)

        hep_rfm.parallel.Worker(jh, _func, args=(queue,), kwargs={'extra': e})

    jh.process()

    for _ in range(n):

        v = queue.get()

        assert v % e == 0

    queue.close()
