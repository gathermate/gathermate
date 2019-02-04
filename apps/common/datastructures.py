# -*- coding: utf-8 -*-

import logging as log
from copy import deepcopy


class MultiDict(dict):
    """
    werkzeug.datastructures.MultiDict
    """
    def __init__(self, mapping=None):
        if mapping is None:
            dict.__init__(self, {})
        else:
            if isinstance(mapping, MultiDict):
                dict.__init__(self, ((k, l) for k, l in mapping.iterlists()))
            elif isinstance(mapping, dict):
                tmp = {}
                for key, value in mapping.iteritems():
                    if isinstance(value, (tuple, list)):
                        if len(value) == 0:
                            continue
                        value = list(value)
                    else:
                        value = [value]
                    tmp[key] = value
                dict.__init__(self, tmp)
            else:
                tmp = {}
                for key, value in mapping:
                    tmp.setdefault(key, []).append(value)
                dict.__init__(self, tmp)

    def __getstate__(self):
        return dict(self.lists())

    def __setstate__(self, value):
        dict.clear(self)
        dict.update(self, value)

    def __getitem__(self, key):
        if key in self:
            list_ = dict.__getitem__(self, key)
            if len(list_) > 0:
                return list_[0]
        raise KeyError(key)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, [value])

    def __repr__(self):
        return  '%s(%r)' % (self.__class__.__name__, list(self.items(multi=True)))

    def add(self, key, value):
        dict.setdefault(self, key, []).append(value)

    def getlist(self, key, type=None):
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            return []
        if type is None:
            return list(value)
        result = []
        for item in value:
            try:
                result.append(type(item))
            except ValueError:
                pass
        return result

    def setlist(self, key, new_list):
        dict.__setitem__(self, key,  list(new_list))

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        else:
            default = self[key]
        return default

    def setlistdefault(self, key, default_list=None):
        if key not in self:
            default_list = list(default_list or ())
            dict.__setitem__(self, key, default_list)
        else:
            default_list = dict.__getitem__(self, key)
        return default_list

    def items(self, multi=False):
        for key, values in self.iteritems():
            if multi:
                for value in values:
                    yield key, value
            else:
                yield key, values[0]

    def lists(self):
        for key, values in self.iteritems():
            yield key, list(values)

    def keys(self):
        return self.iterkeys()

    def values(self):
        for values in self.itervalues():
            yield values[0]

    def listvalues(self):
        return self.itervalues()

    def copy(self):
        return self.__class__(self)

    def deepcopy(self, memo=None):
        return self.__class__(deepcopy(self.to_dict(flat=False), memo))

    def to_dict(self, flat=True):
        if flat:
            return dict(self.iteritems())
        return dict(self.lists())

    def update(self, other_dict):
        for key, value in self.iter_multi_items(other_dict):
            MultiDict.add(self, key, value)

    def pop(self, key, default=None):
        try:
            list_ = dict.pop(self, key)
            if len(list_) == 0:
                raise KeyError(key)
            return list_[0]
        except KeyError:
            return default

    def popitem(self):
        try:
            item = dict.popitem(self)
            if len(item[1]) == 0:
                raise KeyError(item)
            return (item[0], item[1][0])
        except KeyError as e:
            raise KeyError(e.args[0])

    def poplist(self, key):
        return dict.pop(self, key, [])

    def popitemlist(self):
        try:
            return dict.popitem(self)
        except KeyError as e:
            raise KeyError(e.args[0])

    def __copy__(self):
        return self.copy()

    def __deppcopy__(self, memo):
        return self.deepcopy(memo=memo)

    def iter_multi_items(self, mapping):
        if isinstance(mapping, MultiDict):
            for item in mapping.items(multi=True):
                yield item
        elif isinstance(mapping, dict):
            for key, value in mapping.iteritems():
                if isinstance(value, (tuple, list)):
                    for value in value:
                        yield key, value
                else:
                    yield key, value
        else:
            for item in mapping:
                yield item

    def get(self, key, default=None, type=None):
        try:
            value = self[key]
        except KeyError:
            return default
        if type is not None:
            try:
                value = type(value)
            except ValueError:
                value = default
        return value
