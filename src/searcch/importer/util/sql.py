
import sqlalchemy
import datetime
import logging
import json

import searcch.importer.db.model
from searcch.importer.db.model import Base

LOG = logging.getLogger(__name__)

conv_type_map = {
    datetime.datetime: {
        "parse": datetime.datetime.fromisoformat,
        "valid": str,
        "typeinfo": "isoformat str"
    },
    bytes: {
        "parse": lambda x: bytes(x,"utf-8"),
        "valid": str,
        "typeinfo": str
    }
}

def object_from_json(session,obj_class,j,skip_primary_keys=True,
                     error_on_primary_key=False,allow_fk=False,should_query=True,
                     obj_cache=[],obj_cache_dicts=[]):
    """
    This function provides hierarchical construction of sqlalchemy objects from JSON.  It handles regular fields and handles recursion ("hierarchy") through relationships.  We use the term hierarchy in the sense that an Artifact may have one or more curations associated with it; so perhaps, less a hierarchy than a tree; but we represent the relationships as children in JSON.  If such "children" have an existing match in the DB, we link those objects directly in (NB: this needs to change to handle permissions or places where we don't want to create a link to existing objects, because the owner needs to ack, or whatever).
    """
    obj_kwargs = dict()

    LOG.debug("object_from_json: %r -> %r" % (obj_class,j))

    if j == None:
        LOG.debug("null json value: %r %r" % (obj_class,j))
        return

    for k in obj_class.__mapper__.column_attrs.keys():
        colprop = getattr(obj_class,k).property.columns[0]
        # Always skip foreign keys; we want caller to use relations.
        if colprop.foreign_keys and k in j and not allow_fk:
            raise ValueError("foreign keys (%s.%s) always disallowed; use relations" % (
                obj_class.__name__,k))
        # Handle primary_key presence carefully.  If skip_primary_keys==True,
        # we will ignore primary_key presence in json, unless
        # error_on_primary_key==True.  If skip_primary_keys==False, we expect
        # primary keys and error without them, unless
        # error_on_primary_key==False .
        if colprop.primary_key:
            # We are willing to ignore primary keys (e.g. for POST, create new
            # artifact)
            if skip_primary_keys == True:
                # ... but we can also be anal and error on primary_key presence
                # entirely.
                if error_on_primary_key and k in j:
                    raise ValueError("disallowed id key %r" % (k,))
                continue
            # But we might also require them
            if skip_primary_keys == False:
                if k not in j:
                    if error_on_primary_key and not colprop.nullable:
                        raise ValueError("missing required key '%s'" % (k))
                    else:
                        continue
                else:
                    # XXX: need to check to see that the caller has permissions
                    # to reference and/or modify this object... quite tricky.
                    # For instance, caller cannot modify Artifact.owner, nor
                    # can a caller modify an extant person, unless themselves.
                    #
                    # We might need to leave this to to
                    # artifact_diff... because we don't know at this point if
                    # we are merely referencing, or if we are modifying.
                    obj_kwargs[k] = j[k]
                    continue

        if k not in j:
            continue

        # Do some basic type checks: python_type equiv, enum validity, length, required.
        if not isinstance(j[k],colprop.type.python_type):
            if colprop.type.python_type in conv_type_map \
              and isinstance(j[k],conv_type_map[colprop.type.python_type]["valid"]):
                try:
                    j[k] = conv_type_map[colprop.type.python_type]["parse"](j[k])
                except:
                    raise ValueError("invalid type for key '%s': should be '%s'" % (
                        k,conv_type_map[colprop.type.python_type]["typeinfo"]))
            elif colprop.nullable and j[k] == None:
                continue
            else:
                raise ValueError("invalid type for key '%s' ('%s'): should be '%s'" % (
                    k,type(j[k]),colprop.type.python_type))
        if hasattr(colprop.type,"length") \
          and colprop.type.length \
          and len(j[k]) > colprop.type.length:
            raise ValueError("value too long for key '%s' (max %d)" % (
                k,colprop.type.length))
        if isinstance(colprop.type,sqlalchemy.sql.sqltypes.Enum) \
          and not j[k] in colprop.type._enums_argument:
            raise ValueError("value for key '%s' not in enumeration set" % (k))

        # Appears valid as far as we can tell.
        obj_kwargs[k] = j[k]

    for k in obj_class.__mapper__.relationships.keys():
        relprop = getattr(obj_class,k).property
        foreign_class = relprop.argument
        if isinstance(foreign_class,str):
            foreign_class = getattr(searcch.importer.db.model,foreign_class)
        if relprop.backref:
            if k in j:
                raise ValueError("disallowed key '%s'" % (k))
            continue
        # Do some basic checks, and if they pass, attempt to load an
        # existing object from the DB.  If there are multiple objects,
        # raise an error; we don't know what to do.  If there are no
        # objects, recurse and try to obtain one.
        if relprop.uselist:
            if k in j and not isinstance(j[k],list):
                raise ValueError("key '%s' must be a list")
            obj_kwargs[k] = []

        if len(relprop.local_columns) > 1:
            raise TypeError("cannot handle relationship with multiple foreign keys")

        # See if this is a relationship that has a foreign key into another
        # table; or if it's a relationship that uses our primary key into
        # another table.
        (lcc,) = relprop.local_columns
        if lcc.foreign_keys:
            # This is a relationship through a foreign key we store in this
            # table, into another table.  So check to see if that key is
            # nullable.
            colprop = getattr(obj_class,lcc.name).property.columns[0]
            if k in j:
                # Then we need to look for existing objects that match this
                # one, and reference them if they exist.  We look in our cache
                # and in the session.
                if obj_cache and obj_cache_dicts:
                    try:
                        cached = obj_cache_dicts.index(j[k])
                        obj_kwargs[k] = obj_cache[cached]
                        continue
                    except:
                        pass
                next_obj = object_from_json(
                    session,foreign_class,j[k],skip_primary_keys=skip_primary_keys,
                    error_on_primary_key=error_on_primary_key,should_query=True,
                    allow_fk=allow_fk,obj_cache=obj_cache,obj_cache_dicts=obj_cache_dicts)
                obj_kwargs[k] = next_obj
                obj_cache.append(next_obj)
                obj_cache_dicts.append(j[k])
                continue
        else:
            # This is a relationship into another table via a key in our
            # table, probably our primary key.  These relationships are
            # fundamentally nullable, so nothing to check, just recurse.
            pass
        if not k in j:
            continue
        if relprop.uselist:
            for x in j[k]:
                next_obj = object_from_json(
                    session,foreign_class,x,skip_primary_keys=skip_primary_keys,
                    error_on_primary_key=error_on_primary_key,should_query=False,
                    allow_fk=allow_fk,obj_cache=obj_cache,obj_cache_dicts=obj_cache_dicts)
                obj_kwargs[k].append(next_obj)
        else:
            next_obj = object_from_json(
                session,foreign_class,j[k],skip_primary_keys=skip_primary_keys,
                error_on_primary_key=error_on_primary_key,should_query=False,
                allow_fk=allow_fk,obj_cache=obj_cache,obj_cache_dicts=obj_cache_dicts)
            obj_kwargs[k] = next_obj

    # Query the DB iff all top-level obj_kwargs are basic types or persistent
    # objects, and if our parent told us we should query.
    if should_query:
        can_query = True
        for kwa in list(obj_kwargs):
            if isinstance(obj_kwargs[kwa],list):
                # This is a relation list, so we can't query for this object
                # like this.
                can_query = False
            if not isinstance(obj_kwargs[kwa],Base):
                continue
            try:
                state = sqlalchemy.inspect(obj_kwargs[kwa])
                can_query = getattr(state, "persistent", False)
            except:
                pass
            if not can_query:
                break
        if can_query:
            q = session.query(obj_class)
            for kwa in list(obj_kwargs):
                q = q.filter(getattr(obj_class,kwa).__eq__(obj_kwargs[kwa]))
            qres = q.all()
            if qres:
                obj_cache.append(qres[0])
                obj_cache_dicts.append(j)
                return qres[0]

    return obj_class(**obj_kwargs)
