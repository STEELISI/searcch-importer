
import logging
import os
import os.path
import datetime

from searcch.importer.extractor import BaseExtractor
from searcch.importer.db.model import (
    ArtifactFileMember,FileContent )

LOG = logging.getLogger(__name__)

class BasicFileExtractor(BaseExtractor):
    """A simple extractor that knows enough to look for (README,LICENSE,COPYING}* if a previous heuristic has not found them."""
    name = "basic_file"
    version = "0.1"

    def __init__(self,config,session,**kwargs):
        self._config = config
        self._session = session

    def add_file_member(self,artifact_file,dirent):
        content = None
        st = dirent.stat()
        mtime = datetime.date.fromtimestamp(st.st_mtime)
        #ctime = datetime.date.fromtimestamp(st.st_ctime)
        size = st.st_size
        try:
            f = open(dirent.path,'rb')
            content = f.read()
            f.close()
        except:
            pass
        fc = FileContent(content=content,size=size)
        rfm = ArtifactFileMember(
            pathname=dirent.name,name=dirent.name,html_url=None,
            download_url=None,filetype="text",
            file_content=fc,size=size,mtime=mtime)
        artifact_file.members.append(rfm)
        return rfm

    def extract(self):
        """Extracts all possible metadata from an artifact import session."""

        #
        # For now, we assume we're looking for our key files in an archive, and
        # that the artifact.files themselves are not README/LICENSE/COPYING
        # (e.g., that they were not associated with the artifact as individual
        # ArtifactFiles, and thus would only be already present as
        # ArtifactFileMembers).  We look for these files in each retrieved file
        # we have (e.g. multiple repos/archives).
        #
        for rf in self.session.retrieved_files:
            # If this is not an archive/repo, skip it.
            if not os.path.isdir(rf.path):
                continue

            # We do not overwrite existing ArtifactFileMembers
            readme = license = copying = citation_cff = None

            for rfm in rf.artifact_file.members:
                if rfm.name.startswith("README"):
                    readme = rfm
                    self.session.add_general_text_from_file(rf,rfm)
                elif rfm.name.startswith("LICENSE"):
                    license = rfm
                elif rfm.name.startswith("COPYING"):
                    copying = rfm
                elif rfm.name == "CITATION.cff":
                    citation_cff = rfm
            if readme and (license or copying) and citation_cff:
                continue

            for dirent in os.scandir(rf.path):
                if dirent.is_symlink():
                    continue
                if not dirent.is_file():
                    continue
                if not readme and dirent.name.startswith("README"):
                    readme = self.add_file_member(rf.artifact_file,dirent)
                    self.session.add_general_text_from_file(rf,readme)
                if not license and dirent.name.startswith("LICENSE"):
                    license = self.add_file_member(rf.artifact_file,dirent)
                if not copying and dirent.name.startswith("COPYING"):
                    copying = self.add_file_member(rf.artifact_file,dirent)
                if not citation_cff and dirent.name == "CITATION.cff":
                    citation_cff = self.add_file_member(rf.artifact_file,dirent)
