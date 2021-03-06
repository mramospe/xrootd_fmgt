__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']

import importlib
import inspect
import os
import pkgutil

__project_path__ = os.path.dirname(os.path.abspath(__file__))


__all__ = []
for loader, module_name, ispkg in pkgutil.walk_packages(__path__):

    __all__.append(module_name)

    if not ispkg:
        # Import all classes and functions
        mod = importlib.import_module('hep_rfm.' + module_name)

        __all__ += mod.__all__

        for n, c in inspect.getmembers(mod):
            if n in mod.__all__:
                globals()[n] = c

# Sort the contents
__all__ = list(sorted(__all__))
