.. _limitations:

Limitations
-----------

The biggest limiting factor concerns hashing **very-large files**.
The functions here present are optimized to work as well with **large files**
(those that can not be completely loaded in memory).
However, for **very-large files (> 20 GB)**, the hashing process might become
very slow depending on the machine.

Another limitation has to do with the **xrootd protocol**.
Oftenly, with the **xrootd protocol** we are **not allowed to copy**
(via *xrdcp*) a file from the local system to the remote.
In case your project uses files which are on a site accessible via
**xrootd protocol**, you might need to define that as your *main* site.
Uploading the new files to this site and then running the update script
from it would be probably the way to go.
