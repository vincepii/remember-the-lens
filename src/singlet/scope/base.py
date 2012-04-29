#! /usr/bin/python

#    Copyright (c) 2011 David Calle <davidc@framli.eu>
#    Copyright (c) 2011 Michael Hall <mhall119@gmail.com>

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os

from gi.repository import GLib, GObject, Gio
from gi.repository import Dee
# FIXME: Some weird bug in Dee or PyGI makes Dee fail unless we probe
#        it *before* we import the Unity module... ?!
_m = dir(Dee.SequenceModel)
from gi.repository import Unity


class ScopeBuilder(type):
    '''
    MetaClass for building Scope classes and subclasses
    '''

    def __new__(cls, name, bases, attrs):
        #import pdb; pdb.set_trace()
        super_new = super(ScopeBuilder, cls).__new__
        parents = [b for b in bases if isinstance(b, ScopeBuilder)]
        if not parents:
            # If this isn't a subclass of ScopeBuilder, don't do anything special.
            return super_new(cls, name, bases, attrs)

        # Create the class.
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})

        attr_meta = attrs.pop('Meta', None)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        base_meta = getattr(new_class, '_meta', None)

        setattr(new_class, '_meta', ScopeMeta(meta))

        setattr(new_class, 'lens', LensTemplate(new_class._meta.lens_name, new_class._meta.categories))

        for aName, a in attrs.items():
            setattr(new_class, aName, a)

        return new_class



class LensTemplate(object):

    def __init__(self, name, categories):
        self.name = name
        
        for index, cat in enumerate(categories):
            setattr(self, cat, index)

class ScopeMeta(object):
    '''
    Metadata object for a Scope
    '''

    def __init__(self, meta):
        self.name = getattr(meta, 'name', '')
        self.lens_name = getattr(meta, 'lens', '')
        self.categories = getattr(meta, 'categories', [])

        self.title = getattr(meta, 'title', self.name.title()+' Scope')
        self.description = getattr(meta, 'description', 'Scope for %s' % self.name.title())

        self.bus_name = getattr(meta, 'bus_name', 'unity.singlet.lens.%s.%s' % (self.lens_name, self.name))
        self.bus_path = getattr(meta, 'bus_path', '/'+str(self.bus_name).replace('.', '/'))

        self.search_on_blank = getattr(meta, 'search_on_blank', False)

class Scope(object):
    __metaclass__ = ScopeBuilder
    
    def __init__(self):
        # Populate scopes
        self._scope = Unity.Scope.new ("%s" % self._meta.bus_path)
        self._scope.connect ("search-changed", self.on_search_changed)
        self._scope.connect ("filters-changed", self.on_filtering_changed);

        self._scope.export()

    def on_search_changed (self, entry, search, search_type, cancellable):
        if search:
            search_string = search.props.search_string
        else:
            search_string = None

        if self._meta.search_on_blank or (search_string is not None and search_string != ''):
            results = search.props.results_model
            results.clear()
            if not cancellable.is_cancelled():
                if search_type == Unity.SearchType.GLOBAL:
                    self.global_search(search_string, results, cancellable)
                else:
                    self.search(search_string, results, cancellable)
        search.finished()

    def on_filtering_changed(self, *_):
        self._scope.queue_search_changed(Unity.SearchType.DEFAULT)
        
    def hide_dash_response(self, uri=''):
        return Unity.ActivationResponse(handled=Unity.HandledType.HIDE_DASH, goto_uri=uri)
        
    def update_dash_response(self, uri=''):
        return Unity.ActivationResponse(handled=Unity.HandledType.SHOW_DASH, goto_uri=uri)
        
    def global_search(self, phrase, results, cancellable):
        return self.search(phrase, results, cancellable)

    def search(self, phrase, results, cancellable):
        pass
