
class ImporterError(Exception):
    """Our generic exception base class."""

class ImporterInternalError(ImporterError):
    """A generic for unanticipated situations and wrapped internal exceptions."""

    def __init__(self,msg,exc_info=None,**kwargs):
        self.wrapped = exc_info
        super(ImporterInternalError,self).__init__(msg,**kwargs)

class ImporterNotFound(ImporterError):
    """No importer can import the given source."""

    def __init__(self,source,*args,**kwargs):
        self.source = source
        msg = "No importer module can import %r" % (source,)
        super(ImporterNotFound,self).__init__(msg,*args,**kwargs)

class ObjectNotFoundError(ImporterError):
    """Referenced object not found in database."""

    def __init__(self,type_,**kwargs):
        self._type = type_
        self._kwargs = kwargs
        self._http_code = 404
        kwargs_msg = ""
        for k in sorted(list(kwargs)):
            if kwargs_msg:
                kwargs_msg += ','
            kwargs_msg += str(k) + "=" + repr(kwargs[k])
        super(ObjectNotFoundError,self).__init__(
            "%s(%s) not found" % (type_,kwargs_msg))

class AlreadyPublishedError(ImporterError):
    """Artifact already published."""

    def __init__(self,id,msg=""):
        self._http_code = 400
        self._artifact_id = id
        realmsg = "artifact(%r) already published" % (id)
        if msg:
            realmsg += ": " + msg
        super(AlreadyPublishedError,self).__init__(realmsg)

class NotPublishedError(ImporterError):
    """Artifact not yet published."""

    def __init__(self,id,msg=""):
        self._http_code = 400
        self._artifact_id = id
        realmsg = "artifact(%r) not yet published" % (id)
        if msg:
            realmsg += ": " + msg
        super(NotPublishedError,self).__init__(realmsg)

class AlreadyExportedError(ImporterError):
    """Referenced object already exported."""

    def __init__(self,type_,**kwargs):
        self._type = type_
        self._kwargs = kwargs
        self._http_code = 404
        kwargs_msg = ""
        for k in sorted(list(kwargs)):
            if kwargs_msg:
                kwargs_msg += ','
            kwargs_msg += str(k) + "=" + repr(kwargs[k])
        super(AlreadyExportedError,self).__init__(
            "%s(%s) already exported" % (type_,kwargs_msg))

class AlreadyImportedError(ImporterError):
    """Referenced object already imported."""

    def __init__(self,type_,**kwargs):
        self._type = type_
        self._kwargs = kwargs
        self._http_code = 404
        kwargs_msg = ""
        for k in sorted(list(kwargs)):
            if kwargs_msg:
                kwargs_msg += ','
            kwargs_msg += str(k) + "=" + repr(kwargs[k])
        super(AlreadyImportedError,self).__init__(
            "%s(%s) already imported" % (type_,kwargs_msg))

class NotExportedError(ImporterError):
    """Referenced object not yet exported."""

    def __init__(self,type_,msg=None,**kwargs):
        self._type = type_
        self._kwargs = kwargs
        self._http_code = 404
        kwargs_msg = ""
        for k in sorted(list(kwargs)):
            if kwargs_msg:
                kwargs_msg += ','
            kwargs_msg += str(k) + "=" + repr(kwargs[k])
        if not msg:
            msg = "not yet exported"
        super(NotExportedError,self).__init__(
            "%s(%s) %r" % (type_,kwargs_msg,msg))

class MalformedArgumentsError(ImporterError):
    """Malformed arguments."""

    def __init__(self,*args):
        self._http_code = 400
        super(MalformedArgumentsError,self).__init__(*args)

class ConfigError(ImporterError):
    """A generic config error class."""

class HttpError(ImporterError):
    """An HTTP operation failed."""

    def __init__(self,code,*args):
        super(HttpError,self).__init__(*args)
        self.code = code
    
class MissingMetadataError(ImporterError):
    """Critical metadata was unavailable."""
