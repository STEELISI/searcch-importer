
import logging
import os
import os.path
import datetime
import sys
import pygit2

from searcch.importer.extractor import BaseExtractor
from searcch.importer.db.model import (
    ArtifactAffiliation, Affiliation, Person)

LOG = logging.getLogger(__name__)

class GitExtractor(BaseExtractor):
    """A simple extractor that extracts branch/author info from a repository."""
    name = "git_extractor"
    version = "0.1"

    def __init__(self, config, session,**kwargs):
        self._config = config
        self._session = session

    def extract(self):
        """Recognizes branch/author info from a git repo."""
        for rf in self.session.retrieved_files:
            if not (rf.artifact_file.filetype == "application/x-git" \
              or os.path.isdir(rf.path + os.path.sep + ".git")):
                continue
            LOG.debug("inspecting git repo %r",rf.path)
            authors = {}
            repo = None
            try:
                repo = pygit2.Repository(rf.path)
            except:
                LOG.warning("failed to load theoretical git repo %r",rf.path)
                LOG.exception(sys.exc_info()[1])
                continue

            head = repo.head
            ref = repo.head.name.split("/")[-1]

            head_commit = repo[repo.head.target]
            for commit in repo.walk(head_commit.id, pygit2.GIT_SORT_NONE):
                # Sort of cheesy, but a quick hack that prevents the author
                # list from blowing out.  We should also just stop at end of
                # branch, but not sure how to do that with repo.walk yet.
                if len(authors) > 10:
                    break
                (name,email) = (commit.author.name,commit.author.email)
                if not (name or email) or email in authors:
                    continue
                authors[email] = name
                if not self.session.artifact.has_author(name=name,email=email):
                    LOG.debug("git extractor found new author %r/%r",name,email)
                    person = Person(name=name,email=email)
                    self.session.artifact.affiliations.append(
                        ArtifactAffiliation(affiliation=Affiliation(person=person)))
