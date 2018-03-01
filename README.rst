=======
hep_rfm
=======

.. image:: https://img.shields.io/travis/mramospe/hep_rfm.svg
   :target: https://travis-ci.org/mramospe/hep_rfm

.. image:: https://img.shields.io/badge/documentation-link-blue.svg
   :target: https://mramospe.github.io/hep_rfm/

.. inclusion-marker-do-not-remove

Provides tools to manage remote and local files using the xrootd and ssh
protocols. This allows, for example, to synchronize remote files with those
in a local cluster.

Considerations:
===============

  * One file can have different paths, but only one of them is used as **source**.
  * If the **source** is modified, this module provides function to update the others accordingly.
  * If any of the other files is modified, an update will remove this modifications, since the **source** will be copied again into its path.
  * Make sure to have the correct rights to access to the sites before using the functions within this module. This prevents having to introduce their associated passwords may times.

Installation:
=============

This package is available on PyPi, so just type:

.. code-block:: bash

   pip install hep-rfm

To use the **latest development version**, clone the repository and install with `pip`:

.. code-block:: bash

   git clone https://github.com/mramospe/hep_rfm.git
   cd hep_rfm
   pip install .
