#! /usr/bin/python

#    Copyright (c) 2011 Vincenzo Pii <vinc.pii@gmail.com>

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version, with the following additional
#    restriction: 
#    you cannot modify or redistribute this program if you don't use your
#    own Remember The Milk API Key and Shared Secret pair, or receive explicit
#    permission from the author (Vincenzo Pii <vinc.pii@gmail.com>) to 
#    include your changes to this program.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

#    This product uses the Remember The Milk API but is not endorsed or
#    certified by Remember The Milk.

import sys
import webbrowser

from gi.repository import GLib

from singlet.lens import SingleScopeLens, ListViewCategory 
from singlet.utils import run_lens
from rtmapi import Rtm
from gi.repository import Unity

from TokenManager import TokenManager
from ListsInfoManager import ListsInfoManager
from AuthManager import AuthManager
from TasksInfoManager import TasksInfoManager

# http://groups.google.com/group/rememberthemilk-api/browse_thread/thread/dcb035f162d4dcc8?pli=1
RAK = "b2d2254113dd2cd9dc773a62c5a9e337"
RSS = "733e05a324352a7d"

RTM_PAGE="http://www.rememberthemilk.com"
ICON="/usr/share/unity/lenses/tasks-lens/tow"
ICON_EXTENSION = ".png"

# String representing the ID for the category fields filter
CATEGORY_FIELD_FILTER_ID = "category"
# String representing the ID for the due date fields filter
DUE_FIELD_FILTER_ID = "due"
# String representing the ID for the priority fields filter
PRIORITY_FIELD_FILTER_ID = "priority"

class TasksLens(SingleScopeLens):

    class Meta:
        name = 'tasks'
        title = 'Search Tasks'
        description = 'Tasks Search'
        search_hint = 'Search Tasks'
        icon = 'tasks.svg'
        category_order = ['tasks']
        filter_order = ['categoryFilter', 'displayedFieldsFilter'] 

    tasks = ListViewCategory("Tasks", 'stock_yes')

    # id, display name, icon, contracted state
    categoryFilter = Unity.RadioOptionFilter.new("categoryFilter", "Sections", None, False)

    # Get the lists names if possible
    catNames = ListsInfoManager.getTheCategoriesListStatically(RAK, RSS)

    # Maps a filter id to the corresponding string to which fitering must be
    # applied. This is necessary to support different languages
    # e.g.: '0': 'Inbox',
    #       '1': 'Work',
    #       '2': 'Personal',
    #       '3': 'Study',
    #       '4': 'Sent'
    categoryIdToNameMappingTable = {}

    # Populate the category map
    for i in range(0, len(catNames)):
        categoryIdToNameMappingTable[str(i)] = catNames[i]

    # Populate the category filters
    if len(categoryIdToNameMappingTable) == 0:
        categoryFilter.add_option('0', "Lens restart needed", None)
    else:
        for i in range(0, len(categoryIdToNameMappingTable)):
            categoryFilter.add_option(categoryIdToNameMappingTable.keys()[i], categoryIdToNameMappingTable.values()[i], None)

    # Populate the ID filters
    displayedFieldsFilter = Unity.CheckOptionFilter.new("fieldsFilter", "Fields to display", None, False) 
    displayedFieldsFilter.add_option(CATEGORY_FIELD_FILTER_ID, "Category", None)
    displayedFieldsFilter.add_option(DUE_FIELD_FILTER_ID, "Due", None)
    displayedFieldsFilter.add_option(PRIORITY_FIELD_FILTER_ID, "Priority", None)

    # Category visualization must be active by default
    displayedFieldsFilter.get_option(CATEGORY_FIELD_FILTER_ID).props.active = True

    # Minimum characters to filter results using the search bar
    MIN_SEARCH_LENGTH = 3
    def __init__ (self):
        super(TasksLens, self).__init__()

        # Object to manage RTM lists
        self._listsInfoManager = ListsInfoManager()

        # Object to manage RTM tasks
        self._tasksInfoManager = TasksInfoManager(self._listsInfoManager)

        # Object to handle the token (save to file, read from file)
        self._tokenManager = TokenManager()

        # RTM auth manager object
        self._authManager = AuthManager(ICON + ICON_EXTENSION, self.tasks)

        # RTM auth token
        self._token = self._tokenManager.readTokenFromFile()

        # RTM object
        self._rtm = Rtm(RAK, RSS, "read", self._token)

    #
    # Update results model (currently disabled)
    #
    def global_search(self, search, model):
        #self._handleSearch(search, model)
        return

    #
    # Update results model
    #
    def search(self, search, model):
        self._handleSearch(search, model)
        return

    def _handleSearch(self, search, model):
        """
        Handles search operations on the lens
        """
        # Authenticate if necessary
        if self._authManager.checkAndRequireAuthentication(self._rtm, model) == True:
            return

        # Download the tasks list
        self._tasksInfoManager.downloadTasksList(self._rtm)
        
        # Get categories filter active option
        try:
            filteredCategoryId = self._scope.get_filter('categoryFilter').get_active_option().props.id
            filteredCategory = self.categoryIdToNameMappingTable[filteredCategoryId]
        except (AttributeError):
            filteredCategory = 'All'
        except (KeyError):
            filteredCategory = 'All'

        # Get fields filter active options
        optionalDisplayFields = []
        for option in self._scope.get_filter('fieldsFilter').options:
            if option.props.active == True:
                optionalDisplayFields.append(option.props.id)

        # Get the tasks for the specified category (all categories are returned
        # filteredCategory doesn't name an existing category)
        tasks = self._tasksInfoManager.getTasksOfCategory(filteredCategory)

        for taskDescriptor in tasks:
            categoryName = taskDescriptor.category if CATEGORY_FIELD_FILTER_ID in optionalDisplayFields else ""
            dueTime = taskDescriptor.due if DUE_FIELD_FILTER_ID in optionalDisplayFields else ""
            priority = taskDescriptor.priority if PRIORITY_FIELD_FILTER_ID in optionalDisplayFields else ""
            name = taskDescriptor.name
            self._updateModel(categoryName, name, dueTime, priority, search, model)

    def _updateModel(self, categoryName, taskName, due, priority, search, model):
        # TODO: priority icons
        if len(due) > 0:
            due = ' ' + '[' + due + ']'

        icon = ICON + priority + ICON_EXTENSION

        if len(search) < self.MIN_SEARCH_LENGTH or search in taskName:
            model.append('rtmLens://select/%s' % taskName,
                icon,
                self.tasks,
                'text/plain',
                categoryName + due,
                taskName,
                '')

    def handle_uri(self, scope, uri):
        action = uri.split('/')[-2]
        word = uri.split('/')[-1]
        print "on_activate_uri: %s %s" % (action, word)
        if action == 'auth':
            self._token = self._authManager.rtmCompleteAuthentication(self._rtm, self._tokenManager)
            # Clear results (icon asking for auth)
            results = self._scope.props.results_model
            results.clear()
            # Update the lens by simulating an empty search
            self.search ("", results)
            return self.update_dash_response()
        elif action == 'select':
            webbrowser.open(RTM_PAGE)

if __name__ == "__main__":
    run_lens(TasksLens, sys.argv)

