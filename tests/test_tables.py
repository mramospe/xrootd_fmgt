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


def test_table( tmpdir ):
    '''
    Test function for the "Table" class.
    '''
    # Test the construction of a table
    f1 = tmpdir.join('f1.txt')
    f2 = tmpdir.join('f2.txt')

    for f in (f1, f2):
        with open(f.strpath, 'wt') as s:
            s.write('first line\n')

    p1 = hep_rfm.FileInfo.from_name_and_path('f1', f1.strpath)
    p2 = hep_rfm.FileInfo.from_name_and_path('f2', f2.strpath)

    table = hep_rfm.Table.from_files([p1, p2])

    ut = table.updated()
    for k in ut:
        assert ut[k] == table[k]

    # Test that the "updated" method updates the required files while
    # keeping the status of the others.
    with open(f2.strpath, 'at') as s:
        s.write('second line\n')

    ut = table.updated(files=['f2'])

    assert ut['f1'] == p1
    assert ut['f2'] != p2

    # Test that a written table is then correctly read
    path = hep_rfm.protocol_path(tmpdir.join('table.txt').strpath)

    table.write(path.path)

    read_table = hep_rfm.Table.read(path.path)

    for k in table:
        assert table[k] == read_table[k]

    # Test generating a backup of a table
    table.write(path.path, backup=True)
    assert os.path.isfile(path.path + '.backup')
    backup_filename = os.path.join(os.path.dirname(path.path), 'backup')
    table.write(path.path, backup=backup_filename)
    assert os.path.isfile(backup_filename)

    # Test warnings
    with pytest.warns(Warning):
        table.write(tmpdir.join('other_path.tb').strpath, backup=True)

    # Test errors raised
    with pytest.raises(IOError):
        table.write(tmpdir.mkdir('other').strpath)


def test_manager( tmpdir ):
    '''
    Test function for the "Manager" class.
    '''
    d1 = tmpdir.mkdir('d1')
    d2 = tmpdir.mkdir('d2')

    # Create two files in the first directory, together with a table
    path11 = os.path.join(d1.strpath, 'file1.txt')
    path12 = os.path.join(d1.strpath, 'file2.txt')

    for p in (path11, path12):
        open(p, 'w')

    f11 = hep_rfm.FileInfo.from_name_and_path('f1', path11)
    f12 = hep_rfm.FileInfo.from_name_and_path('f2', path12)

    table1_path = hep_rfm.protocol_path(os.path.join(d1.strpath, 'table.txt'))

    hep_rfm.Table.from_files([f11, f12]).write(table1_path.path)

    # Define the files for the second directory
    path21 = hep_rfm.protocol_path(os.path.join(d2.strpath, 'file1.txt'))
    path22 = hep_rfm.protocol_path(os.path.join(d2.strpath, 'file2.txt'))

    f21 = hep_rfm.FileInfo('f1', path21)
    f22 = hep_rfm.FileInfo('f2', path22)

    table2_path = hep_rfm.protocol_path(os.path.join(d2.strpath, 'table.txt'))

    hep_rfm.Table.from_files([f21, f22]).write(table2_path.path)

    # Create the manager, with the path to the two tables
    mgr = hep_rfm.Manager()
    mgr.add_table(table1_path.path)
    mgr.add_table(table2_path.path)
    mgr.update()

    # Now the file IDs of both tables must coincide
    t1 = hep_rfm.Table.read(table1_path.path)
    t2 = hep_rfm.Table.read(table2_path.path)

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
