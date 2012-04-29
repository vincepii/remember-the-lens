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


def Category(name, icon, renderer):
    return Unity.Category.new (name, Gio.ThemedIcon.new(icon), renderer)

def IconViewCategory(name, icon):
    return Category(name, icon, Unity.CategoryRenderer.VERTICAL_TILE)

def ListViewCategory(name, icon):
    return Category(name, icon, Unity.CategoryRenderer.HORIZONTAL_TILE)
