Contributing to the `importer`
==============================

Git
---

Work on topic branches in your fork of this project and submit pull requests.

Write good commit messages -- a 72-character summary first line, followed by
separate paragraphs with detail as useful.  Ensure that your `.git/config`
or `~/.gitconfig` contain your preferred name and email.

Always minimize whitespace changes to existing code, even if `pylint` whines.


Python
------

This code base was originally targeted for Python 2/3 compat, to support
legacy users.  That is less a priority at this point; Python 3 is the clear
priority now; but backwards compat is still a nice-to-have.  A handy cheat
sheet is https://python-future.org/compatible_idioms.html .

Run `pylint` over a specific module in your source tree:

    PYTHONPATH=./src pylint searcch.importer.<my.module>

or over the entire thing:

    PYTHONPATH=./src pylint searcch.importer

Our commitment to pylint is obviously lacking, but always a good idea to
comply as much as possible.
