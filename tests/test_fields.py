'''
Test functions for the "fields" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import pytest

# Local
import hep_rfm


def test_check_fields():
    '''
    Test the "check_fields" function.
    '''
    fields = ['p1', 'p2']

    # Check default behaviour
    hep_rfm.fields.check_fields(fields, fields)

    # Test with only one field required
    hep_rfm.fields.check_fields(fields, ['p1'], required=['p1'])

    # Test errors
    with pytest.raises(ValueError):
        hep_rfm.fields.check_fields(fields, ['p1'])

    with pytest.raises(ValueError):
        hep_rfm.fields.check_fields(fields, ['p1'], required=['p2'])


def test_check_function_fields():
    '''
    Test the "check_function_fields" decorator.
    '''
    @hep_rfm.fields.check_function_fields(['p1', 'p2'])
    def function( p1, p2 ):
        ''' Function expecting two arguments '''
        pass

    # Test normal behaviour
    function(p1=1, p2=2)

    # Test errors
    with pytest.raises(ValueError):
        function(p1=1)


def test_construct_from_fields():
    '''
    Test the "construct_from_fields" decorator.
    '''
    class foo(object):

        @hep_rfm.fields.construct_from_fields(['p1', 'p2'])
        def from_fields( cls, **fields ):
            ''' Build the class from fields '''
            pass

    # Test normal behaviour
    foo.from_fields(p1=1, p2=2)

    # Test errors
    with pytest.raises(ValueError):
        foo.from_fields(p1=1)
