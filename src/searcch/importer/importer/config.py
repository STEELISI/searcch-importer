
from searcch.importer.util.config import (
    config_section,ConfigSection )

@config_section
class GithubConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "github"

    @classmethod
    def section_defaults(cls):
        return dict(username="",token="",password="")

@config_section
class GitRepoConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "gitrepo"

    @classmethod
    def section_defaults(cls):
        return dict()

@config_section
class ZenodoConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "zenodo"

    @classmethod
    def section_defaults(cls):
        return dict(token="")
