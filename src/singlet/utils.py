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
import shutil
import subprocess

from gi.repository import GLib, GObject, Gio

import singlet

def run_lens(lens_class, args=None):
    session_bus_connection = Gio.bus_get_sync (Gio.BusType.SESSION, None)
    session_bus = Gio.DBusProxy.new_sync (session_bus_connection, 0, None,
                                          'org.freedesktop.DBus',
                                          '/org/freedesktop/DBus',
                                          'org.freedesktop.DBus', None)
    result = session_bus.call_sync('RequestName',
                                   GLib.Variant ("(su)", (lens_class._meta.bus_name, 0x4)),
                                   0, -1, None)
                                   
    # Unpack variant response with signature "(u)". 1 means we got it.
    result = result.unpack()[0]
    
    if result != 1 :
        print >> sys.stderr, "Failed to own name %s. Bailing out." % lens_class._meta.bus_name
        raise SystemExit (1)
    
    lens = lens_class()
    GObject.MainLoop().run()        

def run_scope(scope_class, args=None):
    session_bus_connection = Gio.bus_get_sync (Gio.BusType.SESSION, None)
    session_bus = Gio.DBusProxy.new_sync (session_bus_connection, 0, None,
                                          'org.freedesktop.DBus',
                                          '/org/freedesktop/DBus',
                                          'org.freedesktop.DBus', None)
    result = session_bus.call_sync('RequestName',
                                   GLib.Variant ("(su)", (scope_class._meta.bus_name, 0x4)),
                                   0, -1, None)
                                   
    # Unpack variant response with signature "(u)". 1 means we got it.
    result = result.unpack()[0]
    
    if result != 1 :
        print >> sys.stderr, "Failed to own name %s. Bailing out." % scope_class._meta.bus_name
        raise SystemExit (1)
    
    scope = scope_class()
    GObject.MainLoop().run()        
