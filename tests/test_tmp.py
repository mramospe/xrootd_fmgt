import test_scripts
import hep_rfm
import tempfile
import os
'''
Hold temporal tests.
'''

__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']

# Python

# Local


def test_table_conversion(tmpdir):
    '''
    Test the conversion of the old table schema to the new table schema.
    '''
    source = tmpdir.join('old_style_table.db')
    target = tmpdir.join('new_style_table.db')

    source.write(
        'file0 /path/to/file0.txt        local  0 none\n'
        'file1 /path/to/file1.txt        local  0 none\n'
        'file2 @host:/path/to/file2.txt  ssh    0 none\n'
        'file3 root://my-site//file3.txt xrootd 0 none\n'
    )

    test_scripts.process(
        'hep-rfm-old-table-to-new {} {}'.format(source, target))

    table = hep_rfm.Table.read(target.strpath)

    assert table['file0'].field('name') == 'file0'
    assert table['file0'].field('path') == '/path/to/file0.txt'
    assert table['file0'].field('pid') == 'local'
    assert table['file0'].field('tmstp') == 0
    assert table['file0'].field('fid') == 'none'

    assert table['file2'].field('path') == '@host:/path/to/file2.txt'
    assert table['file2'].field('pid') == 'ssh'
    assert table['file3'].field('path') == 'root://my-site//file3.txt'
    assert table['file3'].field('pid') == 'xrootd'
