import sys
import os
import re
import collections
import inspect
import json as JSON
import logging
import six
import argparse

"""
The `Applicable` module enables object methods to be called as CLI methods via argparse.  It parses their function signature and docstrings to automatically build the argparse metadata.  See the helpdocs for the Applicable* classes for more information.

To debug `Applicable`, set the `APPLICABLE_DEBUG` environment variable to 1.  This configures a simple, early console logger set to level DEBUG (we need an early logger because your application almost certainly has not yet initialized its logging subsystem yet.
"""

LOG = logging.getLogger(__name__)
if os.getenv("APPLICABLE_DEBUG"):
    logging.basicConfig()
    LOG.setLevel(logging.DEBUG)
DEFAULT_FORMATTER = None

def get_default_formatter():
    return DEFAULT_FORMATTER

class ApplicableMethod(object):
    """
    A decorator class that transforms class methods into argparse
    subcommands that can be invoked from a command-line client.
    
    It allows you to expose methods to application to arguments parsed
    by argparse subcommand parsers.  You decorate functions like::
    
        @ApplicableMethod(
            help="Get a self credential",
            kwargs=[dict(name='force',help='Bypass the cache',
                         action='store_true',default=False)])
        def get_self_credential(self,force=False,cache_notifier=None)
    
    Finally, once you've decorated all the functions you want to expose,
    you need to bind some actual objects to these decorated definitions,
    and create an ApplicableMethod, subcommand-enabled
    :class:`argparse.ArgumentParser` parser.  Here's an example::
    
            import argparse
            import elasticslice.rpc.protogeni as pgrpc
            from elasticslice.util.applicable import Applicable
            
            class DefaultSubcommandArgumentParser(argparse.ArgumentParser):
                __default_subparser = None

                def set_default_subparser(self, name):
                    self.__default_subparser = name

                def _parse_known_args(self, arg_strings, *args, **kwargs):
                    in_args = set(arg_strings)
                    dsp = self.__default_subparser
                    if dsp is not None and not {'-h', '--help'}.intersection(in_args):
                    for x in self._subparsers._actions:
                        subparser_found = (
                        isinstance(x, argparse._SubParsersAction) and
                        in_args.intersection(x._name_parser_map.keys())
                    )
                    if subparser_found:
                        break
                    else:
                        # insert default in first position, this implies no
                        # global options without a sub_parsers specified
                        arg_strings = [dsp] + arg_strings
                return super(DefaultSubcommandArgumentParser,self)._parse_known_args(
                    arg_strings, *args, **kwargs)

                pass
            
            def parse_options():
                parser = DefaultSubcommandArgumentParser()
                parser.add_argument("-d", "--debug", dest="debug", action='store_true',
                                    help="Enable debugging log level")
                parser.add_argument("--config", dest="config_file",
                                    default="~/.protogeni/elasticslice.conf",

                # Add in subparsers.
                subparsers = parser.add_subparsers(help="Subcommands",dest='subcommand')
                subparsers.add_parser('interactive',help="Run in interactive mode")
                Applicable.add_subparsers(subparsers)
                parser.set_default_subparser('interactive')
  
                (options, args) = parser.parse_known_args(sys.argv[1:])
                return (options, args)
            
            (options, args) = parse_options()
            config = Config(options)
            server = pgrpc.ProtoGeniServer(config=config)
            retval = Applicable.apply(options.subcommand,options)
            if type(retval) in [str,int,float]:
                print retval
            else:
                print json.dumps(retval,indent=2)
            pass
    """
    
    def __init__(self,help=None,largs=None,kwargs=None,alias=None,
                 formatter=True,fmtkwargs=None,autofill=True,excluded=None):
        """
        Python class decorators are a bit funny.  First, the class of
        the decorator is instantiated, and is passed all arguments given
        to the ``@decorator()`` invocation.  Second, after decorator
        instantiation, the :func:`__call__` method is called with the
        decorated function object.
        
        :param help: the help string for the subcommand created for this function
        :param largs: list of dicts describing the function's list arguments
        :param kwargs: list of dicts describing the function's keyword arguments
        
        The ``largs`` and ``kwargs`` parameters are used to create an
        :mod:`argparse` subcommand parser that parses parameters you
        want to expose to invocation of the method via CLI/argparse.
        ``largs`` describes your function's list arguments; and
        ``kwargs`` describes your function's keyword arguments.
        ``largs`` and ``kwargs`` are both lists of dicts, where each
        dict describes a function argument.
        
        These dictionaries must have at least one key ('name'); the
        value of the 'name' key must be the actual name of the
        parameter.  If you specify a 'help' key/value pair, that is used
        as the argparse help for for the parameter.  Anything else in
        the dictionary is basically passed to ``parser.add_argument()``
        as a keyword arg.  There are a few exceptions.  Typically, the
        first two arguments to ``parser.add_argument()`` are a short
        option name and a long option name (i.e, ``'-h','--help'``).
        You can customize those by setting a 'parser_largs' key in the
        dict to something like ``['-h','--help']`` (then that list will
        be passed to ``parser.add_arguments(*args)``).  If you specify
        'parser_largs' in this way, it must conform to
        ``parser.add_argument()``'s requirements.  If you do not supply
        the 'parser_largs' key in your parameter dict, we will
        automatically generate the short/long option names by taking the
        first character from the parameter name, and by using the entire
        parameter name, respectively.  If the short option name has
        already been used in the argparser for this function, we will
        not add a short name option for that argument.  Note that for
        the ``largs`` parameter dictionaries, we also add a 'required'
        kwarg when creating the argument parser.  Also note that we add
        a 'dest' kwarg when creating the argument parser, since we have
        to be able to retrieve the parameter value deterministically to
        pass it to the function.  Again, any other keyword in the
        dictionary is passed directly to ``parser.add_argument()`` as a
        kwarg.  This allows the user substantial control over argument
        processing.
        
        You will want to be familiar with the
        :class:`argparse.ArgumentParser` documentation.
 
        For example, if you are decorating the
        :func:`elasticslice.rpc.protogeni.ProtoGeniServer.get_self_credential`
        instance method::
        
            def get_self_credential(self,force=False,cache_notifier=None)
        
        you would invoke the decorator like::
        
            @ApplicableMethod(
                'ProtoGeniServer',
                help="Get a self credential",
                kwargs=[dict(name='force',help='Bypass the cache',
                             action='store_true',default=False)])
        
        Another example: if you are decorating the
        :func:`elasticslice.rpc.protogeni.ProtoGeniServer.create_sliver`
        instance method::
        
            def create_sliver(self,rspec,cm=None,slicename=None,dokeys=True,
                              selfcredential=None,gen_random_key=False):
        
        you would invoke the decorator like::
        
            @ApplicableMethod(
                help="Create a sliver at a CM",
                largs=[dict(name='rspec',help='An RSpec as an XML string'),],
                kwargs=[dict(name='slicename',help='Specify a slice URN'),
                        dict(name='cm',
                             help='Specify a CM; otherwise the default CM will be used'),
                        dict(name='dokeys',help='Install your pubkeys in the sliver',
                             default=True,type=bool),
                        dict(name='gen_random_key',action='store_true',default=False,
                             help='Generate an unencrypted RSA key that will be installed on each node.')],
            )
        """
        self.help = help
        self.largs = largs
        self.kwargs = kwargs
        self.alias = alias
        if type(formatter) == bool and formatter:
            self.formatter = get_default_formatter()
            self.fmtkwargs = None
        else:
            self.formatter = formatter
            self.fmtkwargs = fmtkwargs
            pass
        self.autofill = autofill
        self.excluded = excluded
        # We'll update this in __call__, but the class decorator might also
        # try update it, if there is one.
        self.func = None
        self.module = None
        # Won't know this until class decorator is hit.
        self.cls = None
        self.isinstance = False
        self.isclass = False
        pass

    def __call__(self,func):
        """
        Class decorator method invoked to actually pass in the function.
        
        :param func: the function object being decorated; caller does not
        supply it
        :return: the func passed in -- this decorator does nothing other than
        to record metadata for later invocation of the func.
        """
        func.__dict__['__ApplicableMethod'] = self
        self.func = func
        self.module = inspect.getmodule(func)
        Applicable._autofill_applicable(self)
        return func

    pass

class ApplicableFormatter(object):
    def __init__(self,help=None,largs=None,kwargs=None,
                 autofill=True,excluded=None):
        self.help = help
        self.largs = largs
        self.kwargs = kwargs
        self.autofill = autofill
        self.excluded = excluded
        # Won't know this until __call__
        self.func = None
        self.module = None
        # Won't know this until class decorator is hit.
        self.cls = None
        self.isinstance = False
        self.isclass = False
        pass

    def __call__(self,func):
        """
        Class decorator method invoked to actually pass in the function.
        
        :param func: the function object being decorated; caller does not
        supply it
        :return: the func passed in -- this decorator does nothing other than
        to record metadata for later invocation of the func.
        """
        func.__dict__['__ApplicableFormatter'] = self
        self.func = func
        self.module = inspect.getmodule(func)
        # Formatter functions' first list arg is the result.  So, we need to
        # exclude that from being added as an argparse parameter.
        argspec = inspect.getargspec(func)
        if not argspec.args or len(argspec.args) < 1:
            raise Exception("formatters must accept at least one list arg"
                            " (the result to format); func %s"
                            % (func,))
        elif argspec.args[0] == 'self' and len(argspec.args) < 2:
            raise Exception("instance method formatters must accept at least two"
                            " list args (self, and the result to format); func %s"
                            % (func,))
        name = argspec.args[0]
        if argspec.args[0] == 'self':
            name = argspec.args[1]
            pass
        if self.excluded is None:
            self.excluded = [name]
        else:
            self.excluded.append(name)
            pass
        Applicable._autofill_applicable(self)
        return func

    pass

class ApplicableClass(object):
    def __init__(self):
        self.cls = None
        self.appmethods = list()
        self.appformatters = list()
        pass
    
    def __call__(self,cls):
        self.cls = cls
        for (name,member) in inspect.getmembers(cls):
            if hasattr(member,'__dict__'):
                if '__ApplicableMethod' in member.__dict__:
                    appmethod = member.__dict__['__ApplicableMethod']
                    # Get the "real" class method func object
                    appmethod.func = member
                    appmethod.cls = cls
                    appmethod.module = inspect.getmodule(appmethod.func)
                    self.appmethods.append(appmethod)
                    LOG.info("appmethod %s (%s)" % (str(appmethod),str(member)))
                    Applicable.register_function(appmethod)
                    pass
                elif '__ApplicableFormatter' in member.__dict__:
                    appformatter = member.__dict__['__ApplicableFormatter']
                    # Get the "real" class method func object
                    appformatter.func = member
                    appformatter.cls = cls
                    appformatter.module = inspect.getmodule(appformatter.func)
                    self.appformatters.append(appformatter)
                    LOG.info("appformatter %s (%s)"
                             % (str(appformatter),str(member)))
                    pass
            pass
        return cls
    pass

class InspectedFunction(object):
    """
    Conveniently group info extracted from a function's argspec with
    information extracted from its docstring.
    """
    def __init__(self,func):
        # Maybe supplement missing info from inspection of default values
        # and auto-doc parsing of help strings.
        self.largs = list()
        self.kwargs = dict()
        self.helps = dict()
        self.help = None
        self.isinstance = False
        self.isclass = False
        
        # Try to extract largs/kwargs/defaults
        try:
            argspec = inspect.getargspec(func)
            # First, fill in any holes that metadata can provide.
            if not argspec.defaults is None and len(argspec.defaults) > 0:
                start = len(argspec.args) - len(argspec.defaults)
                self.largs = argspec.args[0:start]
                # Don't include self in the largs we expose via argparse!
                if 'self' in self.largs:
                    self.largs.remove('self')
                    pass
                i = 0
                for argname in argspec.args[start:]:
                    self.kwargs[argname] = argspec.defaults[i]
                    i += 1
                    pass
                pass
            else:
                self.largs = argspec.args
                # Don't include self in the largs we expose via argparse!
                if not self.largs is None and 'self' in self.largs:
                    self.largs.remove('self')
                    pass
                pass
            if not argspec.args is None and len(argspec.args) > 0 \
              and argspec.args[0] == 'self':
                self.isinstance = True
                self.isclass = False
            else:
                self.isinstance = False
                self.isclass = False
                pass
            pass
        except:
            LOG.exception("could not inspect func %s to determine"
                          " instance/class/static/argspec"
                          % (func,))
            pass
        # Try to extract the overall func help string, and any param
        # help strings.
        try:
            if hasattr(func,'__doc__') and func.__doc__ is not None:
                dht = docparse(func.__doc__)
                if dht.params is not None:
                    self.helps = dht.params
                if dht.help is not None:
                    self.help = dht.help
                pass
            pass
        except:
            LOG.exception("could not parse doc string for func %s" % (func))
            pass
        pass
    
    def __repr__(self):
        s = super(InspectedFunction,self).__repr__()
        s = "%s<largs=%s,kwargs=%s,helps=%s,help=%s,isinstance=%s,isclass=%s>" \
           % (s,self.largs,self.kwargs,self.helps,self.help,
              self.isinstance,self.isclass)
        return s
    
    pass

class Applicable(object):
    
    _ARGPMETHODS = dict()
    """
    A class variable where class method metadata is cached prior to creating
    subcommand argparsers.
    """

    _OBJECTS = dict()
    """
    A class variable where registered object instances are saved for
    subcommand->method dispatch.
    """
    
    @staticmethod
    def _argd_merge_ifunc(func,ifunc,argd):
        if not ifunc or not 'name' in argd:
            return
        
        pname = argd['name']
        # Maybe pull help text from inspection
        if not 'help' in argd and pname in ifunc.helps:
            argd['help'] = ifunc.helps[pname]
            pass
        # Maybe pull default value from inspection
        if not 'default' in argd and pname in ifunc.kwargs:
            argd['default'] = ifunc.kwargs[pname]
            pass
        
        LOG.debug("merge: func = %s, ifunc = %s, argd = %s"
                  % (func,ifunc,argd))
        pass
    
    @staticmethod
    def _convert_argd(func,argd,iskwarg=False,shorts=None):
        fname = func.__name__
        if not 'name' in argd:
            raise Exception("must supply name of parameter (%s: %s)!"
                            % (fname,argd))
        
        aplargs = []
        apkwargs = dict(argd)
        parser_largs = None
        if 'parser_largs' in argd:
            parser_largs = argd['parser_largs']
            del apkwargs['parser_largs']
        pname = argd['name']
        del apkwargs['name']
        if not 'help' in argd:
            if False:
                raise Exception("must supply help for parameter (%s: %s)!"
                                % (fname,argd))
            else:
                LOG.warn("should supply help for parameter (%s: %s)!"
                         % (fname,argd))
                pass
            pass
        if parser_largs is not None and len(parser_largs) > 0:
            aplargs = list(parser_largs)
        else:
            if not pname[0] in shorts:
                shorts[pname[0]] = pname
                aplargs = [ '-%s' % (pname[0],),'--%s' % (pname,) ]
            else:
                aplargs = [ '--%s' % (pname,) ]
                pass
            pass
        # Since subcommand args get mashed in with the non-subcommand
        # args, prefix them with ___ as a convention to distinguish.
        # Ugh!  The Config class handles this case specifically above.
        apkwargs['dest'] = '___' + pname
        # And since argparse appears to use dest.toupper() as the metavar,
        # set one if one wasn't already set.
        action = None
        if 'action' in apkwargs:
            action = apkwargs['action']
            pass
        if (not 'metavar' in apkwargs) \
          and (action is None \
                 or action in ['store','append','append_const']):
            apkwargs['metavar'] = pname.upper()
            pass
        # List args are always required.
        if not iskwarg:
            apkwargs['required'] = True
            pass
        return (aplargs,apkwargs,argd)
    
    @staticmethod
    def _autofill_applicable(applicable):
        if not applicable.autofill:
            return
        
        ifunc = InspectedFunction(applicable.func)
        if not ifunc:
            return
        
        LOG.debug("autofill: applicable = %s, func = %s, ifunc = %s"
                  % (applicable,applicable.func,ifunc))
        
        # Handle global help for the method
        if applicable.help is None:
            applicable.help = ifunc.help
            pass
        
        # Process all the list args
        if applicable.largs is not None:
            for _argd in applicable.largs:
                if not applicable.excluded is None \
                  and _argd['name'] in applicable.excluded:
                    continue

                Applicable._argd_merge_ifunc(applicable.func,ifunc,_argd)
                pass
            pass
        elif len(ifunc.largs) > 0:
            # If the user didn't pass in largs, and there are largs,
            # construct them from our inspection of the argspec.
            applicable.largs = list()
            for argname in ifunc.largs:
                if not applicable.excluded is None \
                  and argname in applicable.excluded:
                    continue
                ad = dict(name=argname)
                if argname in ifunc.helps:
                    ad['help'] = ifunc.helps[argname]
                    pass
                applicable.largs.append(ad)
                pass
            pass
        # Process all the keyword args
        _handled_kwargs = []
        if applicable.kwargs is not None:
            for _argd in applicable.kwargs:
                if not applicable.excluded is None \
                  and _argd['name'] in applicable.excluded:
                    continue
                
                Applicable._argd_merge_ifunc(applicable.func,ifunc,_argd)
                _handled_kwargs.append(_argd['name'])
                pass
            pass
        # Any non-excluded, unspecified kwargs that we get from inspection
        # are automatically added as params.
        for ikwarg in ifunc.kwargs.keys():
            if not applicable.excluded is None \
              and ikwarg in applicable.excluded:
                continue
            
            if not ikwarg in _handled_kwargs:
                _argd = dict(name=ikwarg,default=ifunc.kwargs[ikwarg])
                if ikwarg in ifunc.helps:
                    _argd['help'] = ifunc.helps[ikwarg]
                    pass
                if applicable.kwargs is None:
                    applicable.kwargs = list()
                    pass
                applicable.kwargs.append(_argd)
                pass
            pass
        pass
    
    @staticmethod
    def register_function(applicable):
        """
        Register a function as an Applicable function.  Typically this is
        invoked by the decorator; user should never do this directly.
        
        (See the parameter documentation for :func:`__init__`.)
        """
        (func,cls,help,largs,kwargs,alias,formatter,fmtkwargs) = \
          (applicable.func,applicable.cls,applicable.help,applicable.largs,
           applicable.kwargs,applicable.alias,applicable.formatter,
           applicable.fmtkwargs)
         
        #_autofill_applicable(applicable)
        
        if cls is not None and type(cls) != str:
            cls = cls.__name__
            pass
        if cls is None:
            try:
                cls = func.im_class
            except:
                pass
            pass
        module = func.__module__
        fqcp = module
        if cls is not None:
          if type(cls) == str:
            fqcp += '.' + cls
          else:
            fqcp += '.' + cls.__name__
            pass
        LOG.debug('fqcp: %s %s' % (func.__name__,fqcp)) #,str(dir(func)))
        if alias is not None:
            fname = alias
        else:
            fname = func.__name__
        if fname in Applicable._ARGPMETHODS:
            fname = fqcp + ":" + fname
        if fname in Applicable._ARGPMETHODS:
            raise Exception("function %s (in %s) already registered!"
                            % (str(func),fqcp))
        shorts = {}
        # Process the args and get them all setup for argparser instantiation
        newlargs = []
        newkwargs = []

        # Process all the list args
        if largs is not None:
            for _argd in largs:
                newlargs.append(Applicable._convert_argd(func,_argd,iskwarg=False,shorts=shorts))
            pass
        # Process all the keyword args
        if kwargs is not None:
            for _argd in kwargs:
                newkwargs.append(Applicable._convert_argd(func,_argd,iskwarg=True,shorts=shorts))
            pass
        # Process the formatter args
        newfmtkwargs = []
        ## if formatter:
        ##      and '__ApplicableFormatter' in formatter.__dict__:
        ##     #_autofill_applicable(formatter.__dict__['__ApplicableFormatter'])
        ##     pass
        ##     fifunc = InspectedFunction(formatter)
        ##     if fmtkwargs is not None:
        ##         for _argd in fmtkwargs:
        ##             Applicable._argd_merge_ifunc(formatter,fifunc,_argd)
        ##             newfmtkwargs.append(Applicable._convert_argd(func,_argd,iskwarg=True,shorts=shorts))
        ##         pass
        ##     else:
        if formatter and '__ApplicableFormatter' in formatter.__dict__:
            appformatter = formatter.__dict__['__ApplicableFormatter']
            if appformatter.kwargs is not None:
                for _argd in appformatter.kwargs:
                    newfmtkwargs.append(Applicable._convert_argd(func,_argd,iskwarg=True,shorts=shorts))
                    pass
                pass
            pass
                
        # Ok, actually add the metadata we need to generate the argparser
        # and to run the method later on
        Applicable._ARGPMETHODS[fname] = (
            func,alias,cls,module,help,newlargs,newkwargs,formatter,newfmtkwargs)
        pass

    @staticmethod
    def register_object(applicable,name=None):
        """
        Register an instance object (which should be of a type that has
        already been decorated with :class:`ApplicableMethod`).
        
        :param applicable: an instance object, some of whose methods have been decorated with :class:`ApplicableMethod`.
        """
        fqcp = '%s.%s' % (applicable.__module__,applicable.__class__.__name__)
        if name is None:
            pc = fqcp
        else:
            pc = '%s:%s' % (name,fqcp)
            pass
        if pc in Applicable._OBJECTS:
            if name is None:
                raise Exception('default applicable object for class %s'
                                ' already exists!'
                                % (fqcp))
            else:
                raise Exception('named applicable object %s for class %s'
                                ' already exists!'
                                % (name,fqcp))
            pass
        Applicable._OBJECTS[pc] = applicable
        pass

    @staticmethod
    def add_subparsers(subparsers):
        """
        A user should call this method to have :class:`ApplicableMethod`
        add subcommand parsers for all the methods/functions it knows of (i.e,
        that were decorated).
        
        :param subparsers: the argparse action object returned by :func:`argparse.ArgumentParser.add_subparsers`
        """
        keys = sorted(Applicable._ARGPMETHODS.keys())
        for name in keys:
            (func,alias,cls,module,_help,largs,kwargs,formatter,fmtkwargs) = \
                Applicable._ARGPMETHODS[name]
            LOG.debug("adding subparser for %s (%s,%s,%s)" % (name,largs,kwargs,fmtkwargs))
            ap = subparsers.add_parser(name,help=_help)
            for (_largs,_kwargs,argd) in largs:
                ap.add_argument(*_largs,**_kwargs)
                pass
            for (_largs,_kwargs,argd) in kwargs:
                ap.add_argument(*_largs,**_kwargs)
                pass
            for (_largs,_kwargs,argd) in fmtkwargs:
                ap.add_argument(*_largs,**_kwargs)
                pass
            LOG.debug("added subparser %s" % (ap,))
            pass
        pass
    
    @staticmethod
    def apply(method_name,options):
        """
        Apply some argparse'd options to a function, and return its result.
        
        :param method_name: the function name to invoke (i.e., the argparse subcommand that the parser found was invoked).
        :param options: the argparse options Namespace object
        :return: the result of applying the function to the given options
        """
        if not method_name in Applicable._ARGPMETHODS:
            raise Exception("unknown applicable method %s!" % (method_name,))
        
        (_func,alias,cls,module,help,_largs,_kwargs,formatter,_fmtkwargs) = \
            Applicable._ARGPMETHODS[method_name]

        cls_name = cls
        if type(cls) != str:
          cls_name = cls.__name__
        fqcp = '%s.%s' % (module,cls_name)
        if not fqcp in Applicable._OBJECTS:
            #
            # Try the slow way: search the MRO hierarchy for each object.
            #
            for (_fqcp,_obj) in six.iteritems(Applicable._OBJECTS):
                clshier = inspect.getmro(_obj.__class__)
                for _cls in clshier:
                    if _cls.__name__ == cls_name and _cls.__module__ == module:
                        fqcp = _fqcp
                        break
                    pass
                pass
            pass
        if not fqcp in Applicable._OBJECTS:
            raise Exception("no object instance for fully-qualified class %s!"
                            % (fqcp,))
            pass
        obj = Applicable._OBJECTS[fqcp]
        func = getattr(obj,_func.__name__)
        
        args = []
        kwargs = {}

        if _largs is not None:
          for (aplargs,apkwargs,argd) in _largs:
            name = '___' + argd['name']
            args.append(getattr(options,name))
          pass
        if _kwargs is not None:
          for (aplargs,apkwargs,argd) in _kwargs:
            name = '___' + argd['name']
            try:
              kwargs[argd['name']] = getattr(options,name)
            except:
              LOG.exception("missing kwarg param %s" % (argd['name'],))
              pass
            pass
          pass
        LOG.debug("running %s on %s,%s" % (func,args,kwargs))
        LOG.debug("_largs=%s,_kwargs=%s,options=%s" % (_largs,_kwargs,options))
        result = func(*args,**kwargs)
        if formatter is not None:
            #print str(dir(obj))
            #ffunc = getattr(obj,formatter.__name__)
            fmtkwargs = {}
            if _fmtkwargs is not None:
                for (aplargs,apkwargs,argd) in _fmtkwargs:
                    name = '___' + argd['name']
                    try:
                        fmtkwargs[argd['name']] = getattr(options,name)
                    except:
                        LOG.exception("missing fmtkwarg param %s" % (argd['name'],))
                        pass
                    pass
                pass
            LOG.info("fmtkwargs=%s" % (str(fmtkwargs)))
            result = formatter(result,**fmtkwargs)
            pass
        return result

    pass

DocHelpTuple = collections.namedtuple('DocTuple','params returns help')
"""
:attribute params: a dict of param name to help string
:attribute returns: the help string for the return value, if any
:attribute help: the remainder of the function help, sans \\n \\r \\t
"""

DOCP_PARAM_REGEX = \
  re.compile('^\s*:param\s*([a-zA-Z0-9_]+)\s*:\s*(.*)$',
             re.MULTILINE | re.IGNORECASE)
DOCP_PARAM_TYPE_REGEX = \
  re.compile('^\s*:param\s*[^\s]+\s*([a-zA-Z0-9_]+)\s*:\s*(.*)$',
             re.MULTILINE | re.IGNORECASE)
DOCP_RETURN_REGEX = \
  re.compile('^\s*:returns?\s*:\s*(.*)$',
             re.MULTILINE | re.IGNORECASE)
DOCP_RTYPE_REGEX = \
  re.compile('^\s*:rtype?\s*:\s*(.*)$',
             re.MULTILINE | re.IGNORECASE)
DOCP_WS_REGEX = re.compile('[\n\r\t\s]+')

def docparse(doc):
    """
    Parses a Sphinxy Python function's doc string.
    
    :returns: a DocHelpTuple of a parse of a Sphinxy Python function's doc string.
    
    We only find ':param <foo>: ...', ':return(s): <blah>', and the rest is
    assumed to be generic help text.  In the generic help text, we convert
    \\n, \\r, \\t to spaces; then we convert any sequence of multiple spaces
    to a single space.
    """
    params = None
    returns = None
    help = None
    
    d = doc
    m_params = DOCP_PARAM_REGEX.findall(d)
    if m_params is not None and len(m_params) > 0:
        params = dict()
        for (name,help) in m_params:
            params[name] = help.lstrip(' ').rstrip(' ')
            pass
        d = DOCP_PARAM_REGEX.sub('',d)
        pass
    else:
        m_params = DOCP_PARAM_TYPE_REGEX.findall(d)
        if m_params is not None and len(m_params) > 0:
            params = dict()
            for (name,help) in m_params:
                params[name] = help.lstrip(' ').rstrip(' ')
                pass
            d = DOCP_PARAM_TYPE_REGEX.sub('',d)
            pass
    
    m_returns = DOCP_RETURN_REGEX.findall(d)
    if m_returns is not None and len(m_returns) > 0:
        returns = m_returns[0].lstrip(' ').rstrip(' ')
        d = DOCP_RETURN_REGEX.sub('',d)
        pass
    m_returns = DOCP_RTYPE_REGEX.findall(d)
    if m_returns is not None and len(m_returns) > 0:
        returns = m_returns[0].lstrip(' ').rstrip(' ')
        d = DOCP_RTYPE_REGEX.sub('',d)
        pass
    
    d = DOCP_WS_REGEX.sub(' ',d)
    d = DOCP_WS_REGEX.sub(' ',d)
    help = d.lstrip(' ').rstrip(' ')
    
    return DocHelpTuple(params,returns,help)

def _dict_pretty_stringify(result):
    klist = list(result)
    klist.sort()
    retval = []
    for x in klist:
        if type(result[x]) == list:
            retval.append("%s: %s" % (x,",".join([str(y) for y in result[x]])))
        else:
            retval.append("%s: %s" % (x,str(result[x])))
    return "\n".join(retval)

@ApplicableFormatter(
    kwargs=[dict(name='text',action='store_true'),
            dict(name='json',action='store_true')])
def _default_formatter(result,text=None,json=None):
    """
    Format a value as a string or JSON object string.
    
    :param text: display value as plaintext
    :param json: display value as a JSON object
    """
    if json is True:
        LOG.debug("dumping json")
        return JSON.dumps(result,indent=2)
    else:
        LOG.debug("dumping text")
        if type(result) == list:
            newlist = [str(x) for x in result]
            return '\n'.join(newlist)
        elif type(result) == dict:
            return _dict_pretty_stringify(result)
        elif result is None:
            return ""
        else:
            return str(result)
        pass
    pass

DEFAULT_FORMATTER = _default_formatter

class DefaultSubcommandArgumentParser(argparse.ArgumentParser):
    __default_subparser = None

    def set_default_subparser(self, name):
        self.__default_subparser = name

    def _parse_known_args(self, arg_strings, *args, **kwargs):
        in_args = set(arg_strings)
        dsp = self.__default_subparser
        if dsp is not None and not {'-h', '--help'}.intersection(in_args):
            for x in self._subparsers._actions:
                if isinstance(x, argparse._SubParsersAction) \
                  and in_args.intersection(list(x._name_parser_map)):
                    break
        else:
            # insert default in first position, this implies no
            # global options without a sub_parsers specified
            arg_strings = [dsp] + arg_strings
        return super(DefaultSubcommandArgumentParser,self)._parse_known_args(
            arg_strings, *args, **kwargs)
