# Overview

The SEARCCH Hub importer is a tool that partially automates the task of
creating a dataset that describes an artifact.  An artifact is an entity that
the user of the importer wants to identify as a "semantic unit" within the hub.
(Datasets are not atomic: they may contain folders and files.  A dataset is
therefore akin to a tarball or a source-code repository.)

At a high level, the input to the importer is the durable, publicly accessible
location of the artifact to be imported, e.g., a URL or DOI.  The output is a
dataset within the [SEARCCH Hub][1].  The dataset may be edited manually before
it is published within the hub.

The importer can also be used to partially automate the maintenance of existing
datasets within the hub.  This mode is useful, for example, when an artifact
has evolved or changed location.  In this situation, the input to the importer
is (1) the location of the artifact and (2) the identity of the artifact's
existing dataset within the hub.  The output consists of changes to the
existing dataset, bringing it to a state that reflects the updated artifact.
Again, the dataset may be edited manually after the importer has run.  _(ENE:
It would be ideal for the importer to create a new *revision* of the dataset,
ala git.  To my knowledge, however, Clowder does not track revisions of
datasets.)_

For creating new datasets and updating existing ones, the importer may be run
in a mode that does not actually change the contents of the hub.  Instead, the
importer creates a log *describing* the changes that would be made within the
hub.  The importer may also create a script, corresponding to the log, that can
be executed to effect the changes.  _(ENE: This mode is useful for debugging
the importer; for updating datasets when the hub's definitions of artifact
categories and/or metadata is updated; for updating datasets when the importer
itself is updated; for examining the evolution of artifacts; for editing the
update scripts before they are executed; and potentially for logging the
evolution of datasets.)_

The importer is partially controlled by a configuration file (or list of
configuration files), which is an implicit or explicit input to the tool.  The
configuration file is useful, for example, for specifying the values of
metadata that cannot be determined from the artifact itself.  User credentials
for accessing the SEARCCH Hub's API may be contained in a special configuration
file.

The importer has two primary user interfaces.  First, the importer is a
standalone, command-line tool, useful for one-shot use ("import this artifact")
or within scripts.  Second, the importer is the back end for a web form that
helps users of the SEARCCH Hub import artifacts.  The web form is envisioned as
an extension to Clowder and will be implemented in the future.


# Datasets for Artifacts

The importer utilizes [the definition of categories and metadata for
artifacts][2] defined for the SEARCCH Hub.  At the time of this writing, the
categories are the following:

  * Dataset
  * Executable
  * Methodology
  * Metrics
  * Prior Work _(ENE: ?)_
  * Publication
  * Research Questions and Hypothesis
  * Source Code
  * Subject Descriptor/Research Domain
  * Supporting Information

The standard metadata for a dataset include:

  * title
  * owner
  * license information
  * creator(s)
  * description

  * Audience
  * Alternative Title
  * Code (Research code for your experiment)
  * CSDMS Standard Name
  * Date and Time
  * References
  * Grant Number
  * Funding Institution
  * SAS Spatial Geocode
  * ODM2 Variable Name
  * Related Publications
  * artifact type
  * GeoJSON (About Well-known text (WKT))
  * Primary/Initial Publication
  * Principal Investigator(s)
  * SAS Variable Name
  * Time Periods
  * Unit

In addition, certain categories of artifacts have [category-specific
metadata][2].

A dataset can contain folders and files in a typical hierarchy.  Folders have
names.  Files have names and metadata similar to that of datasets.


# Import Process

The goal of the importer is to create a dataset that is an up-to-date
"reflection" of the artifact being processed.  The goal is not to *copy* the
content of the artifact itself, but rather to promote the *discovery* of the
artifact by users of the SEARCCH Hub.  The importer creates a dataset with and
eye toward (1) identifying the artifact, (2) describing the artifact using the
common "language" of the hub, (3) identifying connections/relationships between
the artifact and other artifacts within the hub, and (4) enabling operations on
the artifact, such as deployment to a testbed or converting the artifact into
another form.

Given an artifact, the importer must examine the artifact to determine its
*packaging*, its *category*, and its *structure*.

  * *Packaging* refers to the data format(s) in which the artifact as a whole
    is encoded.  Example types of packaging are "git repository," "tar file,"
    "PDF file," and "VM image."
  * *Category* refers to the general purpose or "logical kind" of the
    artifact.  Possible categories are listed earlier in this document.
  * *Structure* refers to the way in which the components within the artifact
    are organized: i.e., conventions that were followed.  For example, a git
    repository that is organized according to the [Popper
    convention](https://doi.org/10.1109/IPDPSW.2017.157) would be identified as
    such.

Determining the packaging, category, and structure of artifacts will require
the development of heuristics, although it seems likely that a small set of
simple heuristics will be applicable to many artifacts.  For example, a PDF
file is likely to be a "publication," while a git repository containing many
`.c` files is likely to be "source code."  Some repositories, such as GitHub
and common digital libraries, may also provide metadata that can help the
importer to determine the appropriate category for an artifact.


## All Artifacts

The importer records information about the importation process itself in the
metadata of the constructed dataset.  This metadata includes:

  * `importer-name`: the name of the importer tool
  * `importer-version`: the version of the importer tool
  * `import-timestamp`: the time at which the dataset was created
  * `import-schema-version`: the version of the "schema" used by the importer

The importer also records information about the examined artifact and its
packaging, as metadata of the constructed artifact.  Related to the content of
the artifact, this metadata includes:

  * title
  * license information
  * creator(s)
  * `version`: the author-given version of the artifact content, e.g.,
    "1.0.1g"
  * `timestamp`: an author-given timestamp on the artifact content, if any

And relating to the packaging of the artifact:

  * `artifact-location`: the URL or DOI of the artifact
  * `artifact-package-publisher`: (?) the organization or entity that publishes
    the artifact package, e.g., GitHub, Zenodo, or a person
  * `artifact-package-type`: the packaging method, e.g., "git repository"
  * `artifact-package-revision`: identifies the revision, if any, at which
    the package was examined; e.g., a git repository commit or an arXiv paper
    version
  * `artifact-package-timestamp`: the timestamp associated with the (examined
    revision of the) artifact, if any


## Source Code

Source-code artifacts have varied purposes and are available in a variety of
forms.  One source-code artifact may describe a tool that is useful for
experimentation, for example, while another may describe the research software
that accompanies a particular publication.  A source code artifact may refer to
a git repository a GitHub, for example, or to a tarball or zip file.  In
general, given a source-code artifact, the goal of the importer is to identify
the way in which the artifact is packaged; "unpack" the artifact; determine the
structure of the unpacked artifact; and then use heuristics appropriate to that
structure to create a dataset that best "reflects" the artifact.

*Structure* refers to the organization of the parts of an source-code artifact;
i.e., conventions that allow the importer (or a programmer) to navigate the
parts.  For example, it is common for a source-code tree to have a `README`
file in its top-level directory that identifies and describes the source tree.
The `README` contains information that Hub users might look for, and therefore,
that information could be usefully incorporated into the dataset that reflects
the artifact.  Similarly, a top-level `COPYING` or `LICENSE` file can be useful
for identifying the license under which the artifact is made available.

Some sites that store source-code artifacts provide APIs for can be useful for
identifying the structure and properties of a source-code artifact.  For
example, GitHub provides an API that attempts to identify the license(s)
associated with a git repository.


### General strategy

The `artifact type` metadata field the dataset is "Source Code."  The
`structure` metadata field is set to the identified structure of the
source-code artifact.
  
The `description` metadata of the dataset is constructed by summarizing:

  * the contents of the top-level `README` in the artifact
  * the location of the artifact (URL or DOI)
  * the version of the artifact
  * the timestamp of the artifact (e.g., the date associated with the version)

The `languages` metadata of the dataset is set to indicate the principal
programming languages used in the source-code artifact, if this can be
determined.

The importer sets tags on the dataset by matching keywords from the `README`
(and other "important files," see below) against a set of keywords and/or
patterns that correspond to tags.  Tags can be set for other reasons as well;
see the discussion of specific structures, below.

The importer constructs a tree of directories and files within the dataset
toward capturing information form the artifact that is mostly likely to be
useful for making the artifact discoverable in the hub.  The goal is *not* to
describe every file within the artifact; the goal is to identify "important
files" and represent them in the directory tree.  Important files are ones with
content that might reasonably be searched for, or that we want to attach
metadata to.

The important files depend of the structure of the software artifact.  By
default, the importer creates a file in the dataset for every `README` file in
the source-code artifact.  The file in the dataset contains the content of the
original file, so that it can be searched by users of the Hub.  If the `README`
is overly large, the file in the dataset is abbreviated.

The importer sets metadata and tags on the files that it creates within a
dataset.  The `description` is set by summarizing contents of the file, i.e., a
prefix of the file's content.  The `license` and `creator(s)` of the file are
set to match the values of the dataset overall.  Tags are set by scanning the
contents of the file in the source-code artifact against a set or keywords
and/or patterns associated with tags.


### Git

The importer examines a git repository by creating a clone and examining its
contents at a specific revision/tag.  If no revision is explicitly specified to
the importer, the default is the commit currently referenced by the `master`
branch.  The created dataset identifies the revision that was examined, as
described earlier in this document.


### Popper

[Popper](https://falsifiable.us/) is tool and a set of conventions for
conducting computer-based experimental research and organizing the software and
data relating to that research.  If the importer recognizes a git repository as
as Popper workflow, then it adds Popper-specific files to the "important files"
that are represented in the constructed dataset.  These important files
include:

  * `main.workflow`

For examples, see https://github.com/popperized


### CloudLab/Emulab "Git-backed Profiles"

See
http://docs.emulab.net/creating-profiles.html#%28part._repo-based-profiles%29

Important files:

  * `profile.py`

For examples, see https://gitlab.flux.utah.edu/powder-profiles/ota_srslte


# References

[1]: SEARCCH Hub.
https://hub.cyberexperimentation.org/

[2]: SEARCCH Hub Artifact Categorization and Metadata.  Feb 28 2020.
https://docs.google.com/document/d/1T3DrTrI-bPdondwmRuPYL-3kFsH9bJ4qX72eB6hyFto/edit
