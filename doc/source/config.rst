Configuration
=============

Before you run the importer, you may want to create a simple
configuration file.  By default, the importer looks for this config file
in

    ``~/.local/etc/searcch-importer.ini``

You'll want a config file that looks like this::

    [DEFAULT]
    user_email = johnsond@flux.utah.edu
    user_name = johnsond
    
    [github]
    token = 1a6c4be55514fe544b7712309eab910d3dd7c8ba
    
    [zenodo]
    token = ysPeKI7yZ3A2qxSTQ5aqQSSTGbJhga7DhVs7KKzBM3vYtVuYK1bAWzO3hl3N

You should obtain API tokens from Github
(https://github.com/settings/tokens ,
https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
and Zenodo
(https://zenodo.org/account/settings/applications/tokens/new/).  Your
Github and Zenodo tokens should *not* include any scopes; you only need
read-only access to public repositories and records, and to avoid
possible low API rate limits enforced when not using an access token.

By default, the importer will store its imports in a sqlite database
(e.g., ``~/.local/var/searcch-importer.db`` on UNIX-like systems).  You
can change this location (or change the database type and credentials
entirely) like this::

    [db]
    url = sqlite:////tmp/searcch-foo.db

(The value for the ``url`` key is a ``sqlalchemy`` database URL, as
described at
https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls .)

Finally, by default, the importer will automatically upgrade your
database schema each time you run a command that would access the
database, unless you set::

    [db]
    auto_upgrade = false

You should probably leave ``auto_upgrade`` set to ``true`` unless you're
hacking on the importer tool and adding your own migrations.
