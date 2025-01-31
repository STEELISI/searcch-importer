import re
import sys
import six
import logging
import time
import dateutil.parser
import datetime
from future.utils import raise_from
import giturlparse

import github
from github import Github,GithubException

from searcch.importer.importer import BaseImporter
from searcch.importer.exceptions import HttpError
from searcch.importer.db.model import (
    Artifact,ArtifactFile,ArtifactMetadata,ArtifactRelease,User,Person,
    Importer,Affiliation,ArtifactAffiliation,ArtifactFileMember,
    ArtifactTag,FileContent)
from searcch.importer.db.model.license import recognize_license

LOG = logging.getLogger(__name__)

class GithubImporter(BaseImporter):
    """Provides a Github Importer."""

    name = "github"
    version = "0.1"

    @classmethod
    def can_import(cls,url):
        """Checks to see if this URL is a github URL."""
        try:
            url = url.rstrip("/")
            ret = giturlparse.parse(url)
            return ret.github
        except BaseException:
            return False

    def _parse_time(self,timestr):
        #return time.strptime(timestr,"%a, %d %b %Y %H:%M:%S GMT")
        return dateutil.parser.parse(timestr)

    def import_artifact(self,candidate):
        """Imports an artifact from Github and returns an Artifact, or throws an error."""
        url = candidate.url
        LOG.debug("importing '%s' from github" % (url,))
        if "releases" in url:
            url = re.sub(r"releases.*$", "", url)
        url = url.rstrip("/")
        up = giturlparse.parse(url)
        path = up.owner + "/" + up.repo
        pygh_treeish = github.GithubObject.NotSet
        treeish = None
        if hasattr(up,"branch") and up.branch:
            pygh_treeish = treeish = up.branch
        ghkwargs = dict()
        if self.config["github"]["token"]:
            ghkwargs["login_or_token"] = self.config["github"]["token"]
        elif self.config["github"]["username"]:
            ghkwargs["login_or_token"] = self.config["github"]["username"]
            ghkwargs["password"] = self.config["github"]["password"]
        hub = Github(**ghkwargs)
        try:
            repo = hub.get_repo(path)
        except GithubException:
            ex = sys.exc_info()[1]
            raise_from(HttpError(
                ex.status,
                "Failed to get repo object from github API (path %r from url %r): " % (path,url) + ex.data["message"]),ex)

        # Many projects do not fill this stuff out, but most projects do
        # provide a README.  However, we do not glom that into the description;
        # UIs must make the files viewable, especially a README or LICENSE.
        name = repo.full_name
        title = name or urlobj.geturl()
        description = repo.description

        # We try to grab a list of contributors, but there is a ton of
        # variability here.  We hope for a fullname, but if not available, we
        # fall back to the login uid.  The problem for us is that we require an
        # author email.  This is often not exactly available.  So then we have
        # to go through commits!
        authors = {}
        try:
            contributors = repo.get_contributors()
            for contrib in contributors:
                if not contrib.email:
                    continue
                authors[contrib.email] = Person(email=contrib.email,name=contrib.name)
        except:
            pass
        commits = repo.get_commits(pygh_treeish)
        i = 0
        for commit in commits:
            if i > 100:
                break
            i += 1
            try:
                if not commit.author or not commit.author.email:
                    continue
            except:
                continue
            if commit.author.email in authors:
                if commit.author.name:
                    authors[commit.author.email].name = commit.author.name
        affiliations = []
        for email in list(authors):
            LOG.debug("adding author %r",authors[email])
            affiliations.append(ArtifactAffiliation(affiliation=Affiliation(person=authors[email]),roles="Author"))

        metadata = list()
        tags = list()

        # Try to get README/license file contents.  We just use github's
        # heuristics.
        last_modified = repo.last_modified
        if treeish:
            commits[0].last_modified
        rf = ArtifactFile(
            url=url,name=repo.name,filetype="application/x-git",
            mtime=self._parse_time(last_modified))
        files = [rf]
        members = []
        f = None
        try:
            f = repo.get_readme(pygh_treeish)
        except GithubException:
            LOG.warning("%s missing README",url)
        if f:
            fc = FileContent(content=f.decoded_content,size=f.size)
            lines = f.decoded_content.splitlines()
            for l in lines:
                cand=l.decode('utf-8').replace("#", "").strip()
                if (cand != ""):
                    title = cand
                    break
            print("Title ", title)
            afm = ArtifactFileMember(
                pathname=f.path,name=f.name,html_url=f.html_url,
                download_url=f.download_url,filetype="text",
                file_content=fc,size=f.size,
                mtime=self._parse_time(f.last_modified))
            members.append(afm)
        f = None
        try:
            f = repo.get_license()
        except GithubException:
            LOG.warning("%s missing license/copyright",url)
            pass
        license = None
        if f:
            d = FileContent.make_hash(f.decoded_content)
            fc = FileContent(content=f.decoded_content,hash=d,size=f.size)
            afm = ArtifactFileMember(
                pathname=f.path,name=f.name,html_url=f.html_url,
                download_url=f.download_url,filetype="text",
                file_content=fc,size=f.size,
                mtime=self._parse_time(f.last_modified))
            members.append(afm)
            license_short_name = recognize_license(
                f.decoded_content.decode("utf-8"))
            if license_short_name:
                license = self.get_license_object(license_short_name)
        if members:
            rf.members = members

        # Try to extract a list of releases.
        releases = list()
        rel = None
        try:
            rel = repo.get_latest_release()
        except GithubException:
            pass
        if rel:
            rkwargs = dict()
            if rel.author:
                if rel.author.email:
                    rkwargs["author_email"] = rel.author.email
                if rel.author.login:
                    rkwargs["author_login"] = rel.author.login
                if rel.author.name:
                    rkwargs["author_name"] = rel.author.name
            if rel.url:
                rkwargs["url"] = rel.url
            if rel.title:
                rkwargs["title"] = rel.title
            if rel.published_at:
                rkwargs["time"] = rel.published_at
            if rel.tag_name:
                rkwargs["tag"] = rel.tag_name
            if rel.body:
                rkwargs["notes"] = rel.body
            releases.append(ArtifactRelease(**rkwargs))
        if treeish:
            metadata.append(ArtifactMetadata(
                name="ref",value=treeish,source="github"))
        if not treeish:
            metadata.append(ArtifactMetadata(
                name="mtime",value=repo.pushed_at.isoformat(),source="github"))
            metadata.append(ArtifactMetadata(
                name="ctime",value=repo.created_at.isoformat(),source="github"))
        metadata.append(ArtifactMetadata(
            name="clone_url",value=repo.clone_url,source="github"))
        metadata.append(ArtifactMetadata(
            name="git_url",value=repo.git_url,source="github"))
        metadata.append(ArtifactMetadata(
            name="html_url",value=repo.html_url,source="github"))
        if not treeish and repo.default_branch:
            metadata.append(ArtifactMetadata(
                name="default_branch",value=repo.default_branch,source="github"))
        if not treeish and repo.master_branch:
            metadata.append(ArtifactMetadata(
                name="master_branch",value=repo.master_branch,source="github"))
        if repo.full_name:
            metadata.append(ArtifactMetadata(
                name="full_name",value=repo.full_name,source="github"))
        if repo.organization:
            o = repo.organization
            if o.login:
                metadata.append(ArtifactMetadata(
                    name="org_login",value=o.login,source="github"))
            if o.email:
                metadata.append(ArtifactMetadata(
                    name="org_email",value=o.email,source="github"))
            if o.name:
                metadata.append(ArtifactMetadata(
                    name="org_name",value=o.name,source="github"))
            if o.url:
                metadata.append(ArtifactMetadata(
                    name="org_url",value=o.url,source="github"))
        if repo.get_languages():
            metadata.append(ArtifactMetadata(
                name="languages",value=",".join(repo.get_languages().keys()),source="github"))
        metadata.append(ArtifactMetadata(name="size",value=repo.size,source="github"))
        if repo.owner:
            if repo.owner.email:
                metadata.append(ArtifactMetadata(
                    name="owner_email",value=repo.owner.email,source="github"))
            if repo.owner.login:
                metadata.append(ArtifactMetadata(
                    name="owner_login",value=repo.owner.login,source="github"))
            if repo.owner.name:
                metadata.append(ArtifactMetadata(
                    name="owner_name",value=repo.owner.name,source="github"))
        if repo.homepage:
            metadata.append(ArtifactMetadata(
                name="homepage",value=repo.homepage,source="github"))
        metadata.append(ArtifactMetadata(
            name="forks_count",value=repo.forks_count,source="github"))
        metadata.append(ArtifactMetadata(
            name="network_count",value=repo.network_count,source="github"))
        metadata.append(ArtifactMetadata(
            name="stargazers_count",value=repo.stargazers_count,source="github"))
        metadata.append(ArtifactMetadata(
            name="subscribers_count",value=repo.subscribers_count,source="github"))
        metadata.append(ArtifactMetadata(
            name="watchers_count",value=repo.watchers_count,source="github"))
        repo_topics = repo.get_topics()
        if repo_topics:
            for topic in repo_topics:
                ttopic = topic.replace("-"," ")
                tags.append(ArtifactTag(
                    tag=ttopic,source="github"))
            metadata.append(ArtifactMetadata(
                name="topics",value=",".join(repo.get_topics()),source="github"))

        return Artifact(type="software",url=url,title=title,description=description,
                        name=name,ctime=datetime.datetime.now(),ext_id=path,
                        owner=self.owner_object,importer=self.importer_object,
                        tags=tags,meta=metadata,files=files,license=license,releases=releases,
                        affiliations=affiliations)
