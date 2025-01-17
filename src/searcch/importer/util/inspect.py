from __future__ import print_function
import six
from future.utils import iteritems
import logging

LOG = logging.getLogger(__name__)

class FileTypeInspector(object):
    """This class attempts to return one or more mime types and classes (the kind of file, e.g. plain, compressed, archive, image, etc) that are associated with a file.  It returns a list of mime types, from outermost encapsulation to innermost.  It first attempts to use python-magic, then falls back to python-filetype."""

    @classmethod
    def _try_magic(cls,filepath):
        import magic
        f = open(filepath)
        buf = f.read(2048)
        f.close()
        (mime_type,desc) = (
            magic.from_buffer(buf,mime=True),magic.from_buffer(buf))
        im = magic.Magic(decompress=True)
        (inner_mime_type,inner_desc) = (
            im.from_buffer(buf,mime=True),im.from_buffer(buf))
        if not mime_type:
            return None
        if mime_type == inner_mime_type:
            return [(mime_type,desc)]
        else:
            return [(mime_type,desc),(inner_mime_type,inner_desc)]

    @classmethod
    def _try_filetype(cls,filepath):
        import filetype
        kind = filetype.guess(filepath)
        if kind:
            return [(kind.mime,kind.extension)]

    @classmethod
    def inspect(cls,filepath):
        """Returns a list of mime types, from outermost encapsulation to innermost.  Each list item is a tuple (<mime-type>,<description>)."""
        try:
            return cls._try_magic(filepath)
        except:
            pass
        try:
            return cls._try_filetype(filepath)
        except:
            pass
