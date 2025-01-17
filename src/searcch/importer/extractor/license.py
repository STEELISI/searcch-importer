
import logging
import os
import os.path
import datetime
import sys
import commonmark

from searcch.importer.extractor import BaseExtractor
from searcch.importer.util import bytes2str
from searcch.importer.db.model.license import recognize_license

LOG = logging.getLogger(__name__)

class LicenseExtractor(BaseExtractor):
    """A simple extractor that extracts an open-source license from a file."""
    name = "license"
    version = "0.1"

    def __init__(self, config, session,**kwargs):
        self._config = config
        self._session = session

    def recognize_from_path(self,path):
        LOG.debug("recognizing license in %r",path)
        content = None
        with open(path, "rb") as f:
            content = bytes2str(f.read())
        license_short_name = recognize_license(content)
        if license_short_name:
            return self.get_license_object(license_short_name)
        return None

    def extract(self):
        """Recognizes an open-source license from an existing retrieved LICENSE, COPY*"""
        if self.session.artifact.license is not None or self.session.artifact.license_id:
            return

        files = ("LICENSE","LICENSE.md","COPY","COPYING","COPYING.md")

        for rf in self.session.retrieved_files:
            LOG.debug("checking %r for license",rf.path)
            for f in files:
                if not (rf.path.endswith(f) or \
                    (rf.artifact_file.name and rf.artifact_file.name.endswith(f))):
                    continue
                try:
                    license = self.recognize_from_path(rf.path)
                    if license:
                        LOG.debug("extracted %r license from %r",license.short_name,rf.name)
                        self.session.artifact.license = license
                        return
                except:
                    LOG.exception(sys.exc_info()[1])

            # If this is not an archive/repo, skip it.
            if not os.path.isdir(rf.path):
                continue

            for rfm in rf.artifact_file.members:
                LOG.debug("checking %r (%r) for license",rfm.pathname,rfm.name)
                for f in files:
                    if not ((rfm.name and rfm.name.endswith(f)) or rfm.pathname.endswith(f)):
                        continue
                    try:
                        path = rf.path + os.path.sep + rfm.pathname
                        license = self.recognize_from_path(path)
                        if license:
                            LOG.debug("extracted %r license from %r",license.short_name,rfm.pathname)
                            self.session.artifact.license = license
                            return
                    except:
                        LOG.exception(sys.exc_info()[1])
