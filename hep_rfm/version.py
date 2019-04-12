'''
Hold the version of the package.
'''

__author__ = 'Miguel Ramos Pernas'
__email__ = 'miguel.ramos.pernas@cern.ch'

__all__ = ['__version__']

import pkg_resources

try:
    __version__ = pkg_resources.get_distribution('hep_rfm').version
except Exception:
    __version__ = 'unknown'
