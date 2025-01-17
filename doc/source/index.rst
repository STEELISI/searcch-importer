.. searcch-importer documentation master file, created by
   sphinx-quickstart on Thu Sep 10 22:13:07 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

searcch-importer documentation
==============================

``searcch-importer`` (https://gitlab.flux.utah.edu/searcch/importer) is a
tool that imports cybersecurity software metadata, analyzes artifact
source files to extract more metadata, and exports curated artifact
information to the SEARCCH hub---a cybersecurity artifact index.  An
*artifact* is a research product---a codebase, a data set, a
publication, a set of experiments, etc.  The goal of the SEARCCH project
is to provide a powerful index of cybersecurity artifacts.

The ``searcch-importer`` is intended to function both in standalone mode
(e.g. on a contributor's local machine), or within the SEARCCH portal.
This documentation focuses on running the ``searcch-importer`` in
standalone mode.

Currently, the ``searcch-importer`` can import from Github and Zenodo,
and can export to a flattened JSON document.  (Eventually it will export
to the SEARCCH Hub as well.)

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install.rst
   config.rst
   getting-started.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
