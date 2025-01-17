
import logging
import os
import os.path
import datetime
import sys
import commonmark

from searcch.importer.extractor import BaseExtractor
from searcch.importer.db.model import (
    ArtifactFileMember)
from searcch.importer.util import bytes2str

LOG = logging.getLogger(__name__)

class Renderer(object):

    def render(self, ast):
        walker = ast.walker()
        self.txt = ''
        self.d = {}
        self.headingcount = 0
        self.isprevimage = False
        event = walker.nxt()
        while event is not None:
            type_ = event['node'].t
            if hasattr(self, type_):
                getattr(self, type_)(event['node'], event['entering'])
            event = walker.nxt()
        if 'Desc' not in self.d:
          self.d['Desc'] = self.txt
        return self.d

    def prev_img(self):
        self.isprevimage = True

    def prev_paragraph(self):
        self.isprevimage = False

    def out(self, s, is_heading=False):
        if is_heading:
          self.headingcount += 1
          if self.headingcount == 2:
            self.d["Title"] = self.txt.strip()
          elif self.headingcount == 3:
            self.d["Desc"] = self.txt.strip()
          self.txt = ''
        else:
          if not self.isprevimage:
            if len(s) > 1 and len(self.txt) > 0:
              self.txt = self.txt + " " +s.strip()
            else:
              self.txt += s
          else:
            self.isprevimage = False


class TextRenderer(Renderer):

    # Nodes
    def document(self, node, entering):
        pass

    def softbreak(self, node, entering):
        pass

    def linebreak(self, node, entering):
        pass

    def text(self, node, entering):
        self.out(node.literal)

    def emph(self, node, entering):
        pass

    def strong(self, node, entering):
        pass

    def paragraph(self, node, entering):
        self.prev_paragraph()

    def link(self, node, entering):
        pass

    def image(self, node, entering):
        self.prev_img()

    def code(self, node, entering):
        self.out(node.literal)

    def code_block(self, node, entering):
        pass

    def list(self, node, entering):
        pass

    def item(self, node, entering):
        pass
        
    def block_quote(self, node, entering):
        pass

    def heading(self, node, entering):
        self.out(None, True)



class MarkdownExtractor(BaseExtractor):
    """A simple extractor that reads the content from the Readme.md file"""
    name = "markdown_extractor"
    version = "0.1"

    def __init__(self, config, session,**kwargs):
        self._config = config
        self._session = session
        
    def get_filetext(self, path_to_readme):
        try: 
            with open(path_to_readme, "r") as f:
                return f.read()
        except:
            return LOG.exception("Unable to open the readme file")

    def get_data(self, markdown_txt):
        try:
            markdown_txt = bytes2str(markdown_txt)
            parser = commonmark.Parser()
            ast = parser.parse(markdown_txt)
            renderer = TextRenderer()
            return renderer.render(ast)
        except:
            LOG.exception(sys.exc_info()[1])

    def extract(self):
        """Extracts title and description from the Readme.md file"""
        if self.session.artifact.title and self.session.artifact.description:
            return

        for rf in self.session.retrieved_files:
            # If this is not an archive/repo, skip it.
            if not os.path.isdir(rf.path):
                continue
            data = None
            for rfm in rf.artifact_file.members:
                if rfm.name.startswith("README"):
                    path_to_readme = rf.path + os.path.sep + rfm.pathname
                    readme_txt = self.get_filetext(path_to_readme)
                    data = self.get_data(readme_txt)
                    break
            if data:
                LOG.debug("extracted %r from artifact file %r",data,rfm.name)
                if not self.session.artifact.title and data.get("Title", None):
                    self.session.artifact.title = data['Title']
                if not self.session.artifact.description and data.get("Desc", None):
                    self.session.artifact.description = data['Desc']
                break
            else:
                LOG.debug("failed to extract title/desc from artifact %r",self.session.artifact.url)
