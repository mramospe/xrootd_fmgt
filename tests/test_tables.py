'''
Test functions for the "tables" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import os
import pytest
import tempfile

# Local
import hep_rfm


def test_fileinfo():
    '''
    Test for the "FileInfo" class.
    '''
    f = hep_rfm.FileInfo('dummy', 'my/path')

    # It is an inmutable object
    with pytest.raises(AttributeError):
        f.name = 'new'

    assert f.marks.tmstp == hep_rfm.tables.__default_tmstp__
    assert f.marks.fid == hep_rfm.tables.__default_fid__

    with tempfile.NamedTemporaryFile() as f:

        proxy = hep_rfm.FileInfo.from_name_and_path('dummy', f.name)

        assert proxy.name == 'dummy'
        assert proxy.path == f.name


def test_filemarks():
    '''
    Test for the "FileMarks" class.
    '''
    m = hep_rfm.FileMarks(0., 'fid')

    # It is an inmutable object
    with pytest.raises(AttributeError):
        m.fid = 'other'


def test_table():
    '''
    Test function for the "Table" class.
    '''
    with tempfile.NamedTemporaryFile() as f1, tempfile.NamedTemporaryFile() as f2:

        p1 = hep_rfm.FileInfo.from_name_and_path('f1', f1.name)
        p2 = hep_rfm.FileInfo.from_name_and_path('f2', f2.name)

        table = hep_rfm.Table([p1, p2])

        ut = table.updated()
        for k in ut:
            assert ut[k] == table[k]

    with tempfile.TemporaryDirectory() as d:

        path = os.path.join(d, 'table.txt')

        table.write(path)

        read_table = hep_rfm.Table.read(path)

        for k in table:
            assert table[k] == read_table[k]


def test_manager():
    '''
    Test function for the "Manager" class.
    '''
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:

        # Create two files in the first directory, together with a table
        path11 = os.path.join(d1, 'file1.txt')
        path12 = os.path.join(d1, 'file2.txt')

        for p in (path11, path12):
            open(p, 'w')

        f11 = hep_rfm.FileInfo.from_name_and_path('f1', path11)
        f12 = hep_rfm.FileInfo.from_name_and_path('f2', path12)

        table1_path = os.path.join(d1, 'table.txt')

        hep_rfm.Table([f11, f12]).write(table1_path)

        # Define the files for the second directory
        path21 = os.path.join(d2, 'file1.txt')
        path22 = os.path.join(d2, 'file2.txt')

        f21 = hep_rfm.FileInfo('f1', path21)
        f22 = hep_rfm.FileInfo('f2', path22)

        table2_path = os.path.join(d2, 'table.txt')

        hep_rfm.Table([f21, f22]).write(table2_path)

        # Create the manager, with the path to the two tables
        mgr = hep_rfm.Manager()
        mgr.add_table(table1_path)
        mgr.add_table(table2_path)
        mgr.update()

        # Now the file IDs of both tables must coincide
        t1 = hep_rfm.Table.read(table1_path)
        t2 = hep_rfm.Table.read(table2_path)

        for k in t1:
            # Only the name and file IDs must coincide
            f1, f2 = t1[k], t2[k]

            assert f1.name == k
            assert f1.name == f2.name
            assert f1.marks.fid == f2.marks.fid

        # It should return the first one
        t = hep_rfm.Table.read(mgr.available_table())

        assert 'f1' in t
        assert 'f2' in t
