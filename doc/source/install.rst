Installation
============

You can install ``searcch-importer`` in any of the normal Python ways.
Most likely, you'll want to install it locally, not system wide.  You
can install into a ``virtualenv``
(https://docs.python-guide.org/dev/virtualenvs/), or into your local
user account.

The importer supports both Python 2 and 3, but you should use Python 3
if at all possible.


`virtualenv` Install
--------------------

Change to a directory where you'd like to store your virtualenv dir
(e.g., ``/tmp``).  Then run the following commands to install
``searcch-importer`` without manually grabbing a copy of the source::

    virtualenv --python python3 venv
    source venv/bin/activate
    pip install git+https://gitlab.flux.utah.edu/searcch/importer.git


Local Install
-------------

You can install ``searcch-importer`` in your home directory (e.g.,
``~/.local`` on UNIX-like systems) like this::

    pip install --user git+https://gitlab.flux.utah.edu/searcch/importer.git


Source Code Install
-------------------

If you have a copy of the source code
(https://gitlab.flux.utah.edu/searcch/importer), you can run this
command in the source code directory::

    python setup.py install --user

This will install the importer and its dependencies in your home
directory (e.g., ``~/.local`` on UNIX-like systems).
