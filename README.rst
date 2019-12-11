=======
hep_rfm
=======

.. image:: https://img.shields.io/travis/mramospe/hep_rfm.svg
   :target: https://travis-ci.org/mramospe/hep_rfm

.. image:: https://img.shields.io/badge/documentation-link-blue.svg
   :target: https://mramospe.github.io/hep_rfm/

.. image:: https://codecov.io/gh/mramospe/hep_rfm/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/mramospe/hep_rfm

.. inclusion-marker-do-not-remove

Provides tools to manage remote and local files using the XROOTD and/or SSH
protocols.
This allows, for example, to synchronize remote files with those
in a local cluster.
One has to be sure to have the correct rights to access to the sites before using the functions within this module.
This prevents having to introduce their associated passwords many times.

.. _installation:

Installation
============

This package is available on PyPi, so just type:

.. code-block:: bash

   pip install hep-rfm

To use the **latest development version**, clone the repository and install with `pip`:

.. code-block:: bash

   git clone https://github.com/mramospe/hep_rfm.git
   cd hep_rfm
   pip install .
