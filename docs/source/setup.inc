.. _setup:

Setting-up the system
---------------------

The first thing needed to profit from the different tools offered in this
package is to start **defining the set of files** to work with, this means,
a :class:`hep_rfm.Table` object.
A :class:`hep_rfm.Table` is simply a dictionary with strings as keys,
corresponding to the names of the files, and as values,
:class:`hep_rfm.FileInfo` objects.
The latter stores the information needed by this package to work.
This information corresponds to:

- **Name**: this is the user identifier of the file. \
  In a table there can only be one file with the same name.
- **Path**: the path to the file. This can be either a local or remote path.
- **Protocol ID (PID)**: name of the protocol to be used to access the file.
- **Time-stamp**: the system time-stamp of the file, stored as a float value. \
  This will be needed to determine which files are newer.
- **File ID (FID)**: this is the result of hashing the file. For this purpose, the \
  function :func:`hep_rfm.rfm_hash` is used. \
  The result allows to evaluate the integrity of the file, and to determine if \
  two files aiming to be the same are different. Afterwards, the time-stamp \
  will be used to determine which one is newer.

Generally, it will become difficult for the user to generate a table by hand
even using the functions here provided.
A much easier method, makes use of the script **hep-rfm-table**, supplied
together with this package.
**This script allows to create, modify and update tables directly from the
terminal**, avoiding the creation of custom python scripts for that purpose.
To start-up, create a empty directory and then type:

.. code-block:: console

   $ hep-rfm-table -h

You can now see the different options we have to work with tables.
We will start by creating a new table.

.. code-block:: console

   $ hep-rfm-table create table.db
   $ ls
   table.db

We can see the contents on the table at any point by typing

.. code-block:: console

   $ hep-rfm-table display table.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:41.593218
   - Contents:
   No entries found

which is telling us that there are no entries in the table.
Let's add some then.
We will start by creating a new file, with some content, and then we will add it to the table.

.. code-block:: console

   $ echo "My first table file" >> file1.txt
   $ hep-rfm-table add table.db file1 file1.txt
   $ hep-rfm-table display table.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:41.904134
   - Contents:
   name 	path                                                	pid  	tmstp                     	fid                    
   file1	/home/user/rfm/file1.txt	local	2019-04-12 12:54:41.755092	202444300d48c9387406...

So we have added our first file.
In order to do this we had to give the name of the file and the path to it.
You can see that we have added a file named *file1*, that the path to the file has been automatically expanded, to match a global path, and that the time-stamp and file ID have been extracted.
Now let's create two more files and add them to the table as well.

.. code-block:: console

   $ echo "This is the second file" >> file2.txt
   $ echo "This is the third file" >> file3.txt
   $ hep-rfm-table add_massive table.db file2.txt file3.txt
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:42.226468
   - Contents:
   name 	path                                                	pid  	tmstp                     	fid                    
   file1	/home/user/rfm/file1.txt	local	2019-04-12 12:54:41.755092	202444300d48c9387406...
   file2	/home/user/rfm/file2.txt	local	2019-04-12 12:54:42.067091	cad9a71a7902d13f44db...
   file3	/home/user/rfm/file3.txt	local	2019-04-12 12:54:42.067091	ce53225da9b363e3db71...

With this command one can add easily new files, given only their paths, where
the names will be extracted from the name of the files themselves, without
extensions.
Frequently one will have a whole system of files stored in different directories
and subdirectories.
This can easlity handed running another mode, which will take all the files
within a directory and add them to the table.
We can also specify a regular expression, so only the files whose names
(including the extension) match that given.

.. code-block:: console

   $ mkdir -p subdir/subsubdir
   $ echo "This is the fourth file" >> subdir/file4.txt
   $ echo "This is the fifth file" >> subdir/subsubdir/file5.txt
   $ echo "This is the sixth file" >> subdir/subsubdir/file6.dt
   $ hep-rfm-table add_from_dir table.db . --regex .*.txt
   $ hep-rfm-table display table.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:42.643200
   - Contents:
   name 	path                                                                 	pid  	tmstp                     	fid                    
   file1	/home/user/rfm/file1.txt                 	local	2019-04-12 12:54:41.755092	202444300d48c9387406...
   file2	/home/user/rfm/file2.txt                 	local	2019-04-12 12:54:42.067091	cad9a71a7902d13f44db...
   file3	/home/user/rfm/file3.txt                 	local	2019-04-12 12:54:42.067091	ce53225da9b363e3db71...
   file4	/home/user/rfm/subdir/file4.txt          	local	2019-04-12 12:54:42.487090	8a9dcf90d2a0bcb95d8f...
   file5	/home/user/rfm/subdir/subsubdir/file5.txt	local	2019-04-12 12:54:42.487090	86f2f9bb445df1e62818...

You can see that we have included all files in the current directory, but from
*file6.dt*, which did not match the given regular expression.
If we remove the regular expression requirement, then it is included

.. code-block:: console

   $ hep-rfm-table add_from_dir table.db .
   $ hep-rfm-table display table.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:42.970372
   - Contents:
   name 	path                                                                 	pid  	tmstp                     	fid                    
   file1	/home/user/rfm/file1.txt                 	local	2019-04-12 12:54:41.755092	202444300d48c9387406...
   file2	/home/user/rfm/file2.txt                 	local	2019-04-12 12:54:42.067091	cad9a71a7902d13f44db...
   file3	/home/user/rfm/file3.txt                 	local	2019-04-12 12:54:42.067091	ce53225da9b363e3db71...
   file4	/home/user/rfm/subdir/file4.txt          	local	2019-04-12 12:54:42.487090	8a9dcf90d2a0bcb95d8f...
   file5	/home/user/rfm/subdir/subsubdir/file5.txt	local	2019-04-12 12:54:42.487090	86f2f9bb445df1e62818...
   file6	/home/user/rfm/subdir/subsubdir/file6.dt 	local	2019-04-12 12:54:42.487090	5bd329091112ab1c7125...
   table	/home/user/rfm/table.db                  	local	2019-04-12 12:54:42.639090	e00f13b293897a73ea58...

You can see that we have also included the table itself.
This is very dangerous, and must be avoided, since it will lead to a replacement
of the table files when working with :class:`hep_rfm.Manager`.
Usually it is preferred that the files are located in a sub-directory, and the
table file in the parent directory, so there are no conflicts.
To return to a safe status, let's remove the table entry, put everything on a
new directory and add the files again.

.. code-block:: console

   $ hep-rfm-table remove table.db --files table
   $ hep-rfm-table display table.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:43.297370
   - Contents:
   name 	path                                                                 	pid  	tmstp                     	fid                    
   file1	/home/user/rfm/file1.txt                 	local	2019-04-12 12:54:41.755092	202444300d48c9387406...
   file2	/home/user/rfm/file2.txt                 	local	2019-04-12 12:54:42.067091	cad9a71a7902d13f44db...
   file3	/home/user/rfm/file3.txt                 	local	2019-04-12 12:54:42.067091	ce53225da9b363e3db71...
   file4	/home/user/rfm/subdir/file4.txt          	local	2019-04-12 12:54:42.487090	8a9dcf90d2a0bcb95d8f...
   file5	/home/user/rfm/subdir/subsubdir/file5.txt	local	2019-04-12 12:54:42.487090	86f2f9bb445df1e62818...
   file6	/home/user/rfm/subdir/subsubdir/file6.dt 	local	2019-04-12 12:54:42.487090	5bd329091112ab1c7125...
   $ mkdir files
   $ mv subdir *.txt files/.
   $ hep-rfm-table add_from_dir table.db files
   $ hep-rfm-table display table.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:43.628105
   - Contents:
   name 	path                                                                       	pid  	tmstp                     	fid                    
   file1	/home/user/rfm/files/file1.txt                 	local	2019-04-12 12:54:41.755092	202444300d48c9387406...
   file2	/home/user/rfm/files/file2.txt                 	local	2019-04-12 12:54:42.067091	cad9a71a7902d13f44db...
   file3	/home/user/rfm/files/file3.txt                 	local	2019-04-12 12:54:42.067091	ce53225da9b363e3db71...
   file4	/home/user/rfm/files/subdir/file4.txt          	local	2019-04-12 12:54:42.487090	8a9dcf90d2a0bcb95d8f...
   file5	/home/user/rfm/files/subdir/subsubdir/file5.txt	local	2019-04-12 12:54:42.487090	86f2f9bb445df1e62818...
   file6	/home/user/rfm/files/subdir/subsubdir/file6.dt 	local	2019-04-12 12:54:42.487090	5bd329091112ab1c7125...

So now the entry *table* has been removed.
The idea behind this is not only to have a way to keep our data files organized,
but also to be able to **keep files synchronized** in different hosts.
This means that we will have a *main* place, where we would be preferably
placing our new versions of the files, and from there we would be updating the
other locations.
In order to do any modification on a remote we need to authenticate, and
we would need to do it for every single file we want to update.
Using **ssh keys** is thus the preferred way to handle this inconvenient,
or make sure that the target host is directly accessible from your current one.
In the **remote host**, we will need to have **another table** with the paths
in it.
However, we should **specify the path but not the time-stamp or file ID**, since
we will not have a file there.
This is solved adding the *-\\-bare* option to *add* and *add_massive*.
The mode *add_from_dir* will not make sense to be used here, since we do not
have files there.
This means that we could type

.. code-block:: console

   $ ssh username@host.com
   $ mkdir files
   $ hep-rfm-table create table.db
   $ hep-rfm-table add table.db files/file1.txt --bare --remote ssh @host.com
   $ hep-rfm-table display table.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:43.928512
   - Contents:
   name 	path                                	pid  	tmstp	fid 
   file1	@host.com:/home/user/rfm/files/file1.txt	local	0.0  	none

So you can see that the time-stamp and file ID are filled with default values,
which are chosen so they do not cause conflicts.
Note that we have **specified the remote** with the protocol ID *ssh* and the prepending string *@host.com*.
This will be needed afterwards to correctly update the files.
The other files will be added in a row, by typing

.. code-block:: console

   $ hep-rfm-table add_massive table.db `for i in {2..6};do echo files/file$i.txt; done` --bare --remote ssh @host.com
   $ hep-rfm-table display table.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:44.011354
   - Contents:
   name 	path                                	pid  	tmstp	fid 
   file1	@host.com:/home/user/rfm/files/file1.txt	local	0.0  	none
   file2	@host.com:/home/user/rfm/files/file2.txt	local	0.0  	none
   file3	@host.com:/home/user/rfm/files/file3.txt	local	0.0  	none
   file4	@host.com:/home/user/rfm/files/file4.txt	local	0.0  	none
   file5	@host.com:/home/user/rfm/files/file5.txt	local	0.0  	none
   file6	@host.com:/home/user/rfm/files/file6.txt	local	0.0  	none

Note that here we have included all the files in the same directory.
Files do not need to have similar paths in different hosts.

Sometimes we might need to replicate a table, this is, create an entire copy of
the structure of one table (the system of directories and file names) into
another.
This is done through the *replicate* mode:

.. code-block:: console

   $ hep-rfm-table create rtable.db
   $ mkdir rfiles
   $ hep-rfm-table replicate rtable.db table.db files rfiles
   $ hep-rfm-table display rtable.db
   Running "hep-rfm-table" from hep_rfm 0.0.0.dev4
   - Table created with hep_rfm 0.0.0.dev4
   - Last update: 2019-04-12 12:54:44.123548
   - Contents:
   name 	path                                                                        	pid  	tmstp              	fid 
   file1	/home/user/rfm/rfiles/file1.txt                 	local	1970-01-01 01:00:00	none
   file2	/home/user/rfm/rfiles/file2.txt                 	local	1970-01-01 01:00:00	none
   file3	/home/user/rfm/rfiles/file3.txt                 	local	1970-01-01 01:00:00	none
   file4	/home/user/rfm/rfiles/subdir/file4.txt          	local	1970-01-01 01:00:00	none
   file5	/home/user/rfm/rfiles/subdir/subsubdir/file5.txt	local	1970-01-01 01:00:00	none
   file6	/home/user/rfm/rfiles/subdir/subsubdir/file6.dt 	local	1970-01-01 01:00:00	none


You can see that we have created a new table *rtable.db* with the same
structure as *table.txt*, but this time pointing to bare files in the directory
*rfiles*.
There is some policy regarding adding new files through the *replicate* mode
if they already exist in the table.
Options to raise and error, replace the contents or omit the changes are
contemplated.

For more information, you can always run any mode with *-h*.
One we have done this, we are ready to see how we can access the files
and keep data updated in both sites, in the next section: :ref:`file-management`.
