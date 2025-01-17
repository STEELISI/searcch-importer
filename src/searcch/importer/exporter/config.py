
from searcch.importer.util.config import (
    config_section,ConfigSection )

@config_section
class SearcchConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "searcch"

    @classmethod
    def section_defaults(cls):
        return dict(api_key="",api_root="http://localhost/v1")
