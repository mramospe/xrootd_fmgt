'''
Test functions to check that all the modules and members in the package have at
least one test function.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']


# Python
import ast
import importlib
import inspect
import os

# Local
import hep_rfm

# Modules to exclude from having tests
EXCLUDE_MODULES = {'core', 'cpython', 'version'}


def test_all_modules_have_tests():
    '''
    Test that the modules have at least one test. There must one script with
    the name "test_<module name>".
    '''
    f = filter(lambda s: inspect.ismodule(getattr(hep_rfm, s)), hep_rfm.__all__)
    modules = set(map(lambda s: s.lower(), f))

    path = os.path.dirname(__file__)

    scripts = filter(lambda s: s.endswith('.py'), os.listdir(path))

    tests = set(map(lambda s: s.lower()[5:-3], scripts))

    diff = (modules - tests) - EXCLUDE_MODULES
    if len(diff) != 0:
        raise RuntimeError('The following modules do not have '\
                           'test scripts: "{}"'.format(diff))


def test_all_members_have_tests():
    '''
    Test that all the direct members in "hep_rfm" have at least one test. The
    name of the test must start by

    "test_<name of the member>(_<any other characteristic>)"

    to be considered as good.
    '''
    # Get all the test scripts
    path = os.path.dirname(__file__)

    test_files = filter(lambda s: s.startswith('test') and s.endswith('.py'), os.listdir(path))

    tests = map(importlib.import_module, map(lambda s: s[:-3], test_files))

    # Get all the functions in the test scripts
    test_functions = []
    for t in tests:
        for m in dir(t):

            obj = getattr(t, m)

            if m.startswith('test') and inspect.isfunction(obj):
                test_functions.append(m)

    # Check that there are no functions with the same name in different scripts
    diff_funcs = set(test_functions).difference(test_functions)
    if len(diff_funcs) != 0:
        raise RuntimeError('Some test scripts have functions '\
                           'with the same name: {}'.format(diff_funcs))

    # Get all the members of "hep_rfm"
    fltr = lambda s: not s.startswith('_') and not inspect.ismodule(getattr(hep_rfm, s))
    members = tuple(filter(fltr, hep_rfm.__all__))

    # Check that all the members have a test function defined
    for tm in members:

        start_with = 'test_' + tm.lower()

        if not any(map(lambda s: s.startswith(start_with), test_functions)):
            raise RuntimeError('No test defined for member "{}"'.format(tm))
