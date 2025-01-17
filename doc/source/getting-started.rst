Getting Started
===============

The importer provides a single script: ``searcch-importer``.  If you
run::

    searcch-importer -h

you will see a list of available subcommands::

    usage: searcch-importer [-h] [-d] [-c CONFIG_FILE]
                            {artifact.delete,artifact.export,artifact.import,artifact.list,artifact.publish,artifact.show,db.check,db.upgrade,metadata.add,metadata.delete,tag.add,tag.delete}
                            ...
    
    positional arguments:
      {artifact.delete,artifact.export,artifact.import,artifact.list,artifact.publish,artifact.show,db.check,db.upgrade,metadata.add,metadata.delete,tag.add,tag.delete}
                            Subcommands
        artifact.delete     Delete an artifact.
        artifact.export     Export an artifact. Must be published.
        artifact.import     Import an artifact from a URL.
        artifact.list       List artifacts matching filter parameters.
        artifact.publish    Publish an artifact.
        artifact.show       Show artifact details.
        db.check
        db.upgrade
        metadata.add        Add a metadata pair to an unpublished artifact (adds a
                            new curation).
        metadata.delete     Deletes a metadata pair from an unpublished artifact
                            (adds a new curation).
        tag.add             Add a tag to an unpublished artifact (adds a new
                            curation).
        tag.delete          Deletes a tag from an unpublished artifact (adds a new
                            curation).
    
    optional arguments:
      -h, --help            show this help message and exit
      -d, --debug           Enable debugging log level
      -c CONFIG_FILE, --config-file CONFIG_FILE
                            Path to config file


If you run a subcommand (e.g. ``searcch-importer artifact.list -h``),
you will see subcommand-specific help.


Importing an artifact
---------------------

You can import an artifact like this::

    searcch-importer artifact.import -u https://github.com/vusec/type-after-type


Viewing imported artifacts
--------------------------

You can list imported artifacts like this::

    searcch-importer artifact.list

You can view details (recursively) of an imported artifact like this
(assuming you've imported and not deleted an artifact with ``id`` 1::

    searcch-importer artifact.show -i 1
