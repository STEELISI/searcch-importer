
import six
from future.utils import iteritems, print_function

def unpack_file(path,destdir,basename):
    pass

class Unpacker(object):
    """An Unpacker is a class that can unpack a file.  By unpacking, we mean decompressing and/or unpacking an archive.  The default unpacker attempts to use shutil.unpack_archive, then falls back to executables associated with mime types.  We first attempt to detect the file's mime type"""

    @staticmethod
    def recognize(cls,artifact_file):
        """Inspects <artifact_file> to see if this unpacker """

    @staticmethod
    def unpack(cls,artifact_file,basename=None,destdir=None):
        """Unpacks an ArtifactFile to destdir.  If the content is a single file, we place its decompressed/decoded content in <destdir>/<basename>.  If the content is an archive, we extract it to <destdir>/<basename>/ .  We return an UnpackedFile object; it is the caller's job to remove UnpackedFile content."""
