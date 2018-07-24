.. _setup:

Setting-up the system
=====================

The first thing needed to profit from the different tools offered in this
package is to start **defining the set of files** to work with, this means,
a :class:`hep_rfm.Table` object.
A :class:`hep_rfm.Table` is simply a dictionary with strings as keys,
corresponding to the names of the files, and as values, :class:`FileInfo`
objects.
The latter stores the information needed by this package to work.
This information corresponds to:

- **Name**: this is the user identifier of the file. \
  In a table there can only be one file with the same name.
- **Path**: the path to the file. This can be either a local or remote path. \
  In the last case, the possibility to work with both SSH an XROOTD protocols is provided.
- **Time-stamp**: the system time-stamp of the file, stored as a float value. \
  This will be needed to determine which files are newer.
- **File ID**: this is the result of hashing the file. For this purpose, the \
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

   usage: hep-rfm-table [-h]
                        table
                        {create,add,add_massive,add_from_dir,display,remove,update}
                        ...

   Create add elements or update tables. When using remote paths, no check is
   done to determine whether it corresponds to the current host.

   positional arguments:
     table                 Path to the file to store the table
     {create,add,add_massive,add_from_dir,display,remove,update}
                           Mode to run
       create              Create a new empty table
       add                 Add a new file to the table in the given path
       add_massive         Add a list of files to the given table. The name of
                           the files will be used as name for the table index.
       add_from_dir        Add files from a given directory. A regular expression
                           can be used to match those files. Paths will be
                           converted to absolute.
       display             Display the contents of the table at the given path
       remove              Remove the given entries from the table. One can
                           provide both a set of file names and a regular
                           expression.
       update              Update the table located in the given path

   optional arguments:
     -h, --help            show this help message and exit

You can now see the different options we have to work with tables.
We will start by creating a new table.

.. code-block:: console

   $ hep-rfm-table table.db create
   $ ls
   table.db

We can see the contents on the table at any point by typing

.. code-block:: console

   $ hep-rfm-table table.db display
   No entries found in "table.db"

which is telling us that there are no entries in the table.
Let's add some then.
We will start by creating a new file, with a random content, and then we will add it to the table.

.. code-block:: console

   $ echo "My first table file" >> file1.txt
   $ hep-rfm-table table.db add file1 file1.txt
   $ hep-rfm-table table.db display
   Contents of table "table.db"
   name 	path                    	tmstp            	fid                                     
   file1	/home/user/rfm/file1.txt	1532441131.918498	b5f48e2bb67a3f11469f83899195464bda5f149c

So we have added our first file.
In order to do this we had to give the name of the file and the path to it.
You can see that we have added a file named *file1*, that the path to the file has been automatically expanded, to match a global path, and that the time-stamp and file ID have been extracted.
Now let's create two more files and add them to the table as well.

.. code-block:: console

   $ echo "This is the second file" >> file2.txt
   $ echo "This is the third file" >> file3.txt
   $ hep-rfm-table table.db add_massive file2.txt file3.txt
   Contents of table "table.db"
   name 	path                    	tmstp             	fid                                     
   file1	/home/user/rfm/file1.txt	1532468042.6981168	b5f48e2bb67a3f11469f83899195464bda5f149c
   file2	/home/user/rfm/file2.txt	1532468062.7577875	41d87e380cb316535e4a97b523cf7dbfd94eaa80
   file3	/home/user/rfm/file3.txt	1532468067.8457038	02a8fd5d7a7181ba405223b749a0ad9c574ab29b

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
   $ hep-rfm-table table.db add_from_dir . --regex .*.txt
   $ hep-rfm-table table.db display
   Contents of table "table.db"
   name 	path                                     	tmstp             	fid                                     
   file1	/home/user/rfm/file1.txt                 	1532468042.6981168	b5f48e2bb67a3f11469f83899195464bda5f149c
   file2	/home/user/rfm/file2.txt                 	1532468062.7577875	41d87e380cb316535e4a97b523cf7dbfd94eaa80
   file3	/home/user/rfm/file3.txt                 	1532468067.8457038	02a8fd5d7a7181ba405223b749a0ad9c574ab29b
   file4	/home/user/rfm/subdir/file4.txt          	1532468131.9366517	801dabbdf8c7244883a896c418835599103b6ff0
   file5	/home/user/rfm/subdir/subsubdir/file5.txt	1532468142.2924817	220d820bbb8939b69fb7ee028b5144c868cdf499

You can see that we have included all files in the current directory, but from
*file6.dt*, which did not match the given regular expression.
If we remove the regular expression requirement, then it is included

.. code-block:: console

   $ hep-rfm-table table.db add_from_dir .
   $ hep-rfm-table table.db display
   Contents of table "table.db"
   name 	path                                     	tmstp             	fid                                     
   file1	/home/user/rfm/file1.txt                 	1532468042.6981168	b5f48e2bb67a3f11469f83899195464bda5f149c
   file2	/home/user/rfm/file2.txt                 	1532468062.7577875	41d87e380cb316535e4a97b523cf7dbfd94eaa80
   file3	/home/user/rfm/file3.txt                 	1532468067.8457038	02a8fd5d7a7181ba405223b749a0ad9c574ab29b
   file4	/home/user/rfm/subdir/file4.txt          	1532468131.9366517	801dabbdf8c7244883a896c418835599103b6ff0
   file5	/home/user/rfm/subdir/subsubdir/file5.txt	1532468142.2924817	220d820bbb8939b69fb7ee028b5144c868cdf499
   file6	/home/user/rfm/subdir/subsubdir/file6.dt 	1532468149.8963568	0372b573268f3c58d3d4e466607489f57ba17dd3
   table	/home/user/rfm/table.db                  	1532468283.6741607	18c6b58520eff3010c6fd140af092ceeaee2faa3

You can see that we have also included the table itself.
This is very dangerous, and must be avoided, since it will lead to a replacement
of the table files when working with :class:`hep_rfm.Manager`.
Usually it is preferred that the files are located in a sub-directory, and the
table file in the parent directory, so there are no conflicts.
To return to a safe status, let's remove the table entry, put everything on a
new directory and add the files again.

.. code-block:: console

   $ hep-rfm-table table.db remove table
   $ hep-rfm-table table.db display
   Contents of table "table.db"
   name 	path                                     	tmstp             	fid                                     
   file1	/home/user/rfm/file1.txt                 	1532468042.6981168	b5f48e2bb67a3f11469f83899195464bda5f149c
   file2	/home/user/rfm/file2.txt                 	1532468062.7577875	41d87e380cb316535e4a97b523cf7dbfd94eaa80
   file3	/home/user/rfm/file3.txt                 	1532468067.8457038	02a8fd5d7a7181ba405223b749a0ad9c574ab29b
   file4	/home/user/rfm/subdir/file4.txt          	1532468131.9366517	801dabbdf8c7244883a896c418835599103b6ff0
   file5	/home/user/rfm/subdir/subsubdir/file5.txt	1532468142.2924817	220d820bbb8939b69fb7ee028b5144c868cdf499
   file6	/home/user/rfm/subdir/subsubdir/file6.dt 	1532468149.8963568	0372b573268f3c58d3d4e466607489f57ba17dd3
   $ mkdir files
   $ mv subdir *.txt files/.
   $ hep-rfm-table table.db add_from_dir files
   $ hep-rfm-table table.db display
   Contents of table "table.db"
   name 	path                                           	tmstp             	fid                                     
   file1	/home/user/rfm/files/file1.txt                 	1532468042.6981168	b5f48e2bb67a3f11469f83899195464bda5f149c
   file2	/home/user/rfm/files/file2.txt                 	1532468062.7577875	41d87e380cb316535e4a97b523cf7dbfd94eaa80
   file3	/home/user/rfm/files/file3.txt                 	1532468067.8457038	02a8fd5d7a7181ba405223b749a0ad9c574ab29b
   file4	/home/user/rfm/files/subdir/file4.txt          	1532468131.9366517	801dabbdf8c7244883a896c418835599103b6ff0
   file5	/home/user/rfm/files/subdir/subsubdir/file5.txt	1532468142.2924817	220d820bbb8939b69fb7ee028b5144c868cdf499
   file6	/home/user/rfm/files/subdir/subsubdir/file6.dt 	1532468149.8963568	0372b573268f3c58d3d4e466607489f57ba17dd3

So now the entry *table* has been removed.
The idea behind this is not only to have a way to keep our data files organized,
but also to be able to **keep files synchronized** in different hosts.
This means that we will have a *main* place, where we would be preferably
placing our new versions of the files, and from there we would be updating the
other locations.
In order to do any modification on a remote we need to authenticate, and
we would need to do it for every single file we want to update.
Using **SSH keys** is thus the preferred way to handle this inconvenient,
or make sure that the target host is directly accessible from your current one.
In the **remote host**, we will need to have **another table** with the paths
in it.
However, we should **specify the path but not the time-stamp or file ID**, since
we will not have a file there.
This is solved adding the *--bare* option to *add* and *add_massive*.
The mode *add_from_dir* will not make sense to be used here, since we do not
have files there.
This means that we could type

.. code-block:: console

   $ ssh username@host.com
   $ mkdir files
   $ hep-rfm-table table.db create
   $ hep-rfm-table table.db add files/file1.txt --bare --remote @host.com
   $ hep-rfm-table table.db display
   Contents of table "table.db"
   name 	path                                	tmstp             	fid 
   file1	@host.com:/home/user/files/file1.txt	0.0               	none

So you can see that the time-stamp and file ID are filled with default values,
which are chosen so they do not cause conflicts.
Note that we have **specified the remote path "@host.com"**.
This will be needed afterwards to correctly update the files.
The other files will be added in a row, by typing

.. code-block:: console

   $ hep-rfm-table table.db add_massive `a=""; for i in {2..7};do echo file$i.txt; done; echo $a` --bare --remote @host.com
   $ hep-rfm-table table.db display
   Contents of table "table.db"
   name 	path                                                 	tmstp	fid 
   file1	@host.com:/home/user/files/file1.txt                 	0.0  	none
   file2	@host.com:/home/user/files/file2.txt                 	0.0  	none
   file3	@host.com:/home/user/files/file3.txt                 	0.0  	none
   file4	@host.com:/home/user/files/subdir/file4.txt          	0.0  	none
   file5	@host.com:/home/user/files/subdir/subsubdir/file5.txt	0.0  	none
   file6	@host.com:/home/user/files/subdir/subsubdir/file6.txt	0.0  	none

Note that here we have included all the files in the same directory.
Files do not need to have similar paths in different hosts.
One we have done this, we are ready to see how we can access the files
and kee data updated in both sites, in the next section: :ref:`file-management`.
