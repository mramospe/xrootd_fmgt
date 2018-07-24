'''
Test the scripts under the "scripts" directory.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import os
import subprocess

# Local
import hep_rfm


def test_hep_rfm_table( tmpdir ):
    '''
    Test function for the "hep-rfm-table" script.
    '''
    file1_path = tmpdir.join('file1.txt')
    file2_path = tmpdir.join('file2.txt')
    file3_path = tmpdir.join('file3.txt')
    file4_path = tmpdir.join('file4.txt')

    table_path = tmpdir.join('table.txt')

    with file1_path.open('wb') as f:
        f.write(b'file1 text in binary')
    with file3_path.open('wt') as f:
        f.write('file3 text')
    with file4_path.open('wt') as f:
        f.write('file4 text is a bit larger')

    cmds = (
        'hep-rfm-table {} create'.format(table_path),
        'hep-rfm-table {} add {} {}'.format(table_path, 'file1', file1_path),
        'hep-rfm-table {} add {} {} --bare'.format(table_path, 'file2', file2_path),
        'hep-rfm-table {} add_massive {} {}'.format(table_path, file3_path, file4_path),
        'hep-rfm-table {} update'.format(table_path),
        )

    for c in cmds:
        p = subprocess.Popen(c.split())
        assert p.wait() == 0

    table = hep_rfm.Table.read(table_path.strpath)

    for f in table.values():
        f.marks.tmstp != hep_rfm.tables.__default_tmstp__
        f.marks.fid   != hep_rfm.tables.__default_fid__

    # Commands that break
    break_cmds = (
        'hep-rfm-table {} add {} {}'.format(table_path, 'none', tmpdir.join('none.txt')),
    )

    for c in break_cmds:
        p = subprocess.Popen(c.split())
        assert p.wait() != 0
