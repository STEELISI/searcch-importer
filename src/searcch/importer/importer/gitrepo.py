
import sys
import os
import six
import logging
import time
import dateutil.parser
import datetime
from future.utils import raise_from
import giturlparse

from searcch.importer.importer import BaseImporter
from searcch.importer.db.model import (
    Artifact,ArtifactFile,ArtifactMetadata,ArtifactRelease,User,Person,
    Importer,Affiliation,ArtifactAffiliation,ArtifactFileMember )
from searcch.importer.db.model.license import recognize_license

LOG = logging.getLogger(__name__)

class GitRepoImporter(BaseImporter):
    """Provides a Git Repository Importer."""

    name = "gitrepo"
    version = "0.1"

    @classmethod
    def can_import(cls,url):
        """Checks to see if this URL is a git repository."""
        try:
            up = giturlparse.parse(url)
            if os.system("git ls-remote '%s'" % (url,)) == 0:
                return True
            return False
        except BaseException:
            return False

    def _parse_time(self,timestr):
        return dateutil.parser.parse(timestr)

    def import_artifact(self,candidate):
        url = candidate.url
        up = giturlparse.parse(url)
        up_data = up.data
        LOG.debug("up = %r (data = %r)" % (up,up_data))
        rf = ArtifactFile(
            url=url,name=url,filetype="application/x-git")
            #mtime=self._parse_time(repo.last_modified))

        metadata = []
        metadata.append(ArtifactMetadata(
            name="clone_url",value=up.url2https))
        metadata.append(ArtifactMetadata(
            name="git_url",value=up.format("git")))
        metadata.append(ArtifactMetadata(
            name="html_url",value=url))
        if up.branch:
            metadata.append(ArtifactMetadata(
                name="ref",value=up.branch))
        if up.gitlab:
            metadata.append(ArtifactMetadata(
                name="gitlab",value="1"))
        if "isdir" in up_data and up_data["isdir"]:
            metadata.append(ArtifactMetadata(
                name="subpath",value=up.subpath))
            metadata.append(ArtifactMetadata(
                name="subpath_type",value="dir"))
        elif "isfile" in up_data and up_data["isfile"]:
            metadata.append(ArtifactMetadata(
                name="subpath",value=up.subpath))
            metadata.append(ArtifactMetadata(
                name="subpath_type",value="file"))

        return Artifact(
            type="software",url=url,ctime=datetime.datetime.now(),ext_id=url,
            owner=self.owner_object,importer=self.importer_object,
            meta=metadata,files=[rf])
