
import os
import os.path
import subprocess
#import requests
#import requests.utils
import logging
import shutil
import re
import sys

from searcch.importer.util.inspect import FileTypeInspector

LOG = logging.getLogger(__name__)

class RetrievedFile(object):

    def __init__(self,artifact_file,destdir,raw_path,
                 unpacked=None,unpacked_path=None,
                 mime_type=None,mime_desc=None):
        self._artifact_file = artifact_file
        self._destdir = destdir
        self._raw_path = raw_path
        self._unpacked_path = unpacked_path
        if unpacked_path:
            self._unpacked = True
        self._mime_type = mime_type
        self._mime_desc = mime_desc

    @property
    def artifact_file(self):
        return self._artifact_file

    @property
    def artifact(self):
        return self._artifact_file.parent_artifact

    @property
    def destdir(self):
        return self._destdir

    @property
    def raw_path(self):
        return self._raw_path

    @property
    def path(self):
        return self._unpacked_path or self._raw_path

    @property
    def mime_type(self):
        return self._mime_type

    @property
    def mime_desc(self):
        return self._mime_desc

    def set_unpacked_path(self,path):
        self._unpacked = True
        self._unpacked_path = path

    def __repr__(self):
        return "<RetrievedFile(artifact_file=%r,destdir=%r,path=%r,mime_type=%r)>" % (
            self.artifact_file,self.destdir,self.path,self.mime_type)

class GitError(Exception):
    pass
        
class Retriever(object):
    """Helper class to retrieve ArtifactFiles into temp storage, while respecting resource limits.  Understands http(s) and git repos.  ArtifactFiles are stored in <destdir>/raw .  If unspecified, <destdir> defaults to <tmpdir>/artifact.id/artifact_file.id ."""

    def __init__(self,config):
        self._config = config
        self.max_file_size = 0
        if "max_file_size" in config["retrieve"]:
            self.max_file_size = int(config["retrieve"]["max_file_size"])
            if self.max_file_size < 0:
                self.max_file_size = 0

    @property
    def config(self):
        return self._config

    def retrieve(self,artifact_file,artifact,destdir=None,unpack=True):
        import requests
        import requests.utils
        try:
            up = requests.utils.urlparse(artifact_file.url)
            if not up.scheme:
                LOG.info("url '%r' has no scheme",artifact_file.url)
                return None
        except:
            LOG.debug("unparseable url '%r'",artifact_file.url)
            return None
        if not destdir:
            destdir = os.path.join(
                self.config["DEFAULT"]["tmpdir"],str(artifact_file.artifact.id),
                str(artifact_file.id))
        rawpath = os.path.join(destdir,"raw")
        unpacked_path = None
        git = "git"
        if "retrieve" in self.config and "git" in self.config["retrieve"]:
            git = self.config["retrieve"]["git"]
        if artifact_file.filetype == "application/x-git":
            clone_url = artifact_file.url
            ref = None
            for meta in artifact.meta:
                if meta.name == "clone_url":
                    clone_url = meta.value
                if meta.name == "ref":
                    ref = meta.value
            res = subprocess.call(
                [git,"ls-remote",clone_url])
            if res != 0:
                raise FileNotFoundError("repository not found")
            os.makedirs(destdir)
            res = subprocess.call(
                [git,"clone",clone_url,rawpath])
            if res:
                raise GitError("failed to clone %r" % (rawpath,))
            if ref:
                curdir = os.getcwd()
                os.chdir(rawpath)
                res = subprocess.call(
                    [git,"checkout",ref])
                os.chdir(curdir)
                if res:
                    raise GitError("failed to checkout ref %r" % (ref,))
            (mime_type,mime_desc) = ("application/x-git","git")
        else:
            session = requests.session()
            url = artifact_file.url
            if url.startswith("https://ieeexplore.ieee.org/stamp"):
                res = session.get(url,headers={"User-Agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36"})
                if res.status_code == requests.codes.ok:
                    regex = re.compile('.*meta .* content=.* url=(http[^"]+)".*')
                    match = regex.search(res.content.decode())
                    if match:
                        url = match.group(1)
                if url == artifact_file.url:
                    LOG.warning("Failed to download IEEE Xplore URL %r",url)
                    return None
            rawpath = os.path.join(destdir,"raw")
            os.makedirs(destdir)
            head_size = None
            try:
                head_check = session.head(url,allow_redirects=True)
                if head_check.status_code == requests.codes.ok:
                    LOG.debug("length of %r: %r",url,head_check.headers["content-length"])
                    head_size = int(head_check.headers["content-length"])
                else:
                    LOG.debug("length of %r returned %s",url,head_check.status_code)
            except:
                pass
            if self.max_file_size and head_size and head_size > self.max_file_size:
                if not artifact_file.size:
                    artifact_file.size = head_size
                LOG.warn("file %r larger (%d) than max_file_size (%d); skipping fetch",
                         url,head_size,self.max_file_size)
                return None
            response = session.get(url,stream=True)
            response.raise_for_status()
            fd = open(rawpath,'wb')
            total_bytes = 0
            for buf in response.iter_content(4096):
                fd.write(buf)
                total_bytes += len(buf)
                if self.max_file_size and total_bytes > self.max_file_size:
                    LOG.warn("partially-fetched file %r larger than max_file_size (%d); aborting fetch",
                             url,self.max_file_size)
                    fd.close()
                    os.unlink(rawpath)
                    return None
            fd.close()
            if not artifact_file.size:
                artifact_file.size = total_bytes
            (mime_type,mime_desc) = (None,None)
            mimelist = FileTypeInspector.inspect(rawpath)
            if mimelist:
                (mime_type,mime_desc) = mimelist[0]
            if not mime_type:
                try:
                    ct = response.headers["content-type"]
                    idx = ct.find(";")
                    if idx > 0:
                        mime_type = ct[:idx]
                    else:
                        mime_type = ct
                except:
                    pass
            if unpack:
                # XXX: shutil.unpack_archive is only Python >=3.3
                try:
                    extdestdir = os.path.join(destdir,"unpacked")
                    shutil.unpack_archive(rawpath,extdestdir)
                    unpacked_path = extdestdir
                except:
                    pass
        return RetrievedFile(
            artifact_file,destdir,rawpath,
            unpacked_path=unpacked_path,
            mime_type=mime_type,mime_desc=mime_desc)
