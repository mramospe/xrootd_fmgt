'''
Module to process fields in functions and class constructors.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import functools
import logging


__all__ = []


def check_fields( expected, inputs, required = 'all' ):
    '''
    Process two sets of fields, one representing the expected and
    the other those to be used for building a class.
    In case one of the expected fields is not present in the inputs,
    if "required" is set to "all" or the name of the field appears
    in it, a :class:`ValueError` will be raised; otherwise a
    warning is displayed, and the corresponding default value is assumed
    to be used.
    On the other hand, if one of the fields in the inputs does not appear
    in those expected it is omitted, displaying also a warning.

    :param expected: fields expected by a function.
    :type expected: container
    :param inputs: fields provided to the function.
    :type inputs: container
    :raises ValueError: if one of the expected fields is not found in the \
    inputs, and "required" is "all" or the name of the field appears in it.
    '''
    for f in set(expected).difference(inputs):
        if required == 'all' or f in required:
            raise ValueError('Required field "{}" is not present; incompatible version'.format(f))
        else:
            logging.getLogger(__name__).warning('Value for field "{}" not found; setting to default value'.format(f))

    for f in set(inputs).difference(expected):
        logging.getLogger(__name__).warning('Field "{}" not found; ignoring it'.format(f))


def construct_from_fields( expected, required = 'all' ):
    '''
    Decorator for constructors where classes are built using fields.
    '''
    def _wrapper( method ):
        ''' Wrapper around the method '''
        @classmethod
        @functools.wraps(method)
        def __wrapper( *args, **fields ):
            '''
            Check the fields.
            All keyword arguments are considered  as such.
            '''
            check_fields(expected, fields, required)
            return method(*args, **fields)
        return __wrapper
    return _wrapper


def check_function_fields( expected, required = 'all' ):
    '''
    Decorator for functions returning classes which are built using fields.
    '''
    def _wrapper( function ):
        ''' Wrapper around the function '''
        @functools.wraps(function)
        def __wrapper( *args, **fields ):
            '''
            Check the fields.
            All keyword arguments are considered  as such.
            '''
            check_fields(expected, fields, required)
            return function(*args, **fields)
        return __wrapper
    return _wrapper
