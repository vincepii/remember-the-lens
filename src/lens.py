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

# TODO: add a button to show also incomplete tasks
# TODO: use logging system and remove prints
# TODO: package as app
# TODO: add logout button
# TODO: remove the timestamp and build a hastable representation of taskslists
# TODO: aggiungere la callback filters changed

import sys
import webbrowser

from gi.repository import GLib, Gio, GObject, Unity

from singlet.lens import SingleScopeLens, ListViewCategory 
from singlet.utils import run_lens
from rtmapi import Rtm
from gi.repository import Unity

from TokenManager import TokenManager
from ListsInfoManager import ListsInfoManager
from AuthManager import AuthManager
from TasksInfoManager import TasksInfoManager

import locale
import gettext

def init_localization():
    locale.setlocale(locale.LC_ALL, '')
    # take first two characters of country code
    loc = locale.getlocale()
    filename = "../locale/%s.mo" % locale.getlocale()[0][0:2]
    try:
        print "Opening message file {} for locale {}".format(filename, loc[0])
        trans = gettext.GNUTranslations(open(filename, "rb"))
    except IOError:
        print "Using default messages (English)"
        trans = gettext.NullTranslations()
    trans.install()

init_localization()

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
        title = _('Search Tasks')
        description = _('Tasks Search')
        search_hint = _('Search Tasks')
        icon = 'tasks.svg'
        category_order = ['tasks']
        filter_order = ['categoryFilter', 'displayedFieldsFilter', 'orderFilter'] 

    tasks = ListViewCategory(_("Tasks"), 'stock_yes')

    # id, display name, icon, contracted state
    categoryFilter = Unity.RadioOptionFilter.new("categoryFilter", _("Sections"), None, False)

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

    PRIORITIES = {'0': _('Oops, error!'),
                  '1': _('High Priority'),
                  '2': _('Medium Priority'),
                  '3': _('Low Priority'),
                  'N': _('Unspecified')}

    # Populate the category map
    for i in range(0, len(catNames)):
        categoryIdToNameMappingTable[str(i)] = catNames[i]

    # Populate the category filters
    if len(categoryIdToNameMappingTable) == 0:
        categoryFilter.add_option('0', _("Lens restart needed"), None)
    else:
        for i in range(0, len(categoryIdToNameMappingTable)):
            categoryFilter.add_option(categoryIdToNameMappingTable.keys()[i], categoryIdToNameMappingTable.values()[i], None)

    # Populate the ID filters
    displayedFieldsFilter = Unity.CheckOptionFilter.new("fieldsFilter", _("Fields to display"), None, False) 
    displayedFieldsFilter.add_option(CATEGORY_FIELD_FILTER_ID, _("Category"), None)
    displayedFieldsFilter.add_option(DUE_FIELD_FILTER_ID, _("Due"), None)
    displayedFieldsFilter.add_option(PRIORITY_FIELD_FILTER_ID, _("Priority"), None)

    # Populate the ordering filter
    orderFilter = Unity.RadioOptionFilter.new("orderingFilter", _("Sort by"), None, False)
    orderFilter.add_option(TasksInfoManager.ORDERING_PRIORITY_ID, _("Priority"), None)
    orderFilter.add_option(TasksInfoManager.ORDERING_DUE_ID, _("Due dates"), None)
    orderFilter.add_option(TasksInfoManager.ORDERING_NAMES_ID, _("Names"), None)

    # Category visualization must be active by default
    displayedFieldsFilter.get_option(CATEGORY_FIELD_FILTER_ID).props.active = True
    displayedFieldsFilter.get_option(DUE_FIELD_FILTER_ID).props.active = True
    displayedFieldsFilter.get_option(PRIORITY_FIELD_FILTER_ID).props.active = True

    # Priority order as default
    orderFilter.get_option(TasksInfoManager.ORDERING_PRIORITY_ID).props.active = True

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
        self._rtm = Rtm(RAK, RSS, "write", self._token)

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
        # if filteredCategory doesn't name an existing category)
        tasks = self._tasksInfoManager.getTasksOfCategory(filteredCategory)

        # Get the ordering filter status
        try:
            filteringId = self._scope.get_filter('orderingFilter').get_active_option().props.id
        except (AttributeError):
            filteringId = 'Unspecified'
        self._tasksInfoManager.orderTasksList(tasks, filteringId)

        for taskDescriptor in tasks:
            categoryName = taskDescriptor.category if CATEGORY_FIELD_FILTER_ID in optionalDisplayFields else ""
            dueTime = taskDescriptor.prettyDue if DUE_FIELD_FILTER_ID in optionalDisplayFields else ""
            priority = taskDescriptor.priority if PRIORITY_FIELD_FILTER_ID in optionalDisplayFields else ""
            name = taskDescriptor.name
            listId = taskDescriptor.listId
            taskseriesId = taskDescriptor.taskseriesId
            taskId = taskDescriptor.taskId
            self._updateModel(categoryName, name, dueTime, priority, search, model, listId, taskseriesId, taskId)

    def _updateModel(self, categoryName, taskName, due, priority, search, model, listId, taskseriesId, taskId):
        if len(due) > 0:
            due = ' ' + '[' + due + ']'

        icon = ICON + priority + ICON_EXTENSION

        if len(search) < self.MIN_SEARCH_LENGTH or search.lower() in taskName.lower():
            model.append('rtmLens://select/lid={}&tsid={}&tid={}'.format(listId, taskseriesId, taskId),
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

    def _parseModelValue(self, model, taskElement):
        '''
        Takes a model and an iterator to one of the elements and
        returns a dictionary with the elements parsed from model.
        '''
        parsed = {'uri': model.get_value(taskElement, 0),
                'icon': model.get_value(taskElement, 1),
                'tmodel': model.get_value(taskElement, 2),
                'mime': model.get_value(taskElement, 3),
                'catdue': model.get_value(taskElement, 4),
                'taskdesc': model.get_value(taskElement, 5)
                }
        return parsed

    def _getTaskIdsFromUri(self, uri):
        '''
        Parses the URI of a model, which contains the three identifiers of
        a tasks and returns them in a dictionary.

        The input string is like:
        rtmLens://select/lid=20897253&tsid=172048629&tid=273082817

        The output is a dictionary with the following format:
        {'lid': '20897253', 'tid': '273082817', 'tsid': '172048629'}
        where the keys are directly extracted from each id=value pair
        contained in the uri.
        '''
        d = {}
        # Generate a list of key=value pairs (one for each id)
        for ids in (key_value.split('=') for key_value in uri.split('/')[-1].split('&')):
            d[ids[0]] = ids[1]
        return d

    def on_preview_uri(self, scope, uri):
        '''
        Callback method called when the preview for an element is requested
        (i.e., someone right-clicked a task) 
        '''
        identifiers = self._getTaskIdsFromUri(uri)
        model = scope.props.results_model
        current_task = model.get_first_iter()
        last_task = model.get_last_iter()
        # Get, from all the elements, the one that was clicked
        while current_task != last_task:
            if model.get_value(current_task, 0) == uri:
                break
            else:
                current_task = model.next(current_task)
        selectedTaskInfo = self._parseModelValue(model, current_task)
        # Title, description (not visible ?!), icon (set later)
        preview = Unity.GenericPreview.new(selectedTaskInfo['catdue'], selectedTaskInfo['taskdesc'], None)
        preview.props.image_source_uri = selectedTaskInfo['icon']
        icon = Gio.ThemedIcon.new(selectedTaskInfo['icon'])
        preview.props.image = icon
        # Text
        preview.props.description_markup = self._getTaskPreviewDescription(selectedTaskInfo)
        # description, string, icon
        view_action = Unity.PreviewAction.new('complete', _('Complete (disabled)'), None)
        view_action.connect('activated', self.complete_task)
        preview.add_action(view_action)

        # TODO: if task is complete, uncomplete button, ow, complete
        return preview

    def _getTaskPreviewDescription(self, taskInfoDictionary):
        '''
        Reads the dictionary of a task information as built from the model
        ({@see #_parseModelValue) and builds a string to be displayed in
        the preview screen for this task.
        '''
        priority = str(0)
        taskXml = self._listsInfoManager.getTaskByName(
                    self._getTaskIdsFromUri(taskInfoDictionary['uri'])['lid'], 
                    taskInfoDictionary['taskdesc'],
                    self._rtm)
        
        for tasklist in taskXml.tasks:
            for taskseries in tasklist:
                priority = str(taskseries.task.priority)
        catdue = taskInfoDictionary['catdue']
        category = self._getCategoryFromCatDue(catdue)
        s = "<b>" + _("Category") + "</b>: " +  catdue + "\n"
        s += "<b>" + _("Priority") + "</b>: " + self.PRIORITIES[priority] + "\n"
        duedate = self._getDueDateFromCatDue(catdue)
        s += "<b>" + _("Due date") + "</b>: " + duedate + "\n\n"
        s += "<b>" + _("Description") + "</b>\n"
        s += "<i>{}</i>".format(taskInfoDictionary['taskdesc'])
        return s

    def _getCategoryFromCatDue(self, catdue):
        '''
        Takes a "catdue" string (i.e., combination of category and due date,
        e.g., "Work [Mar 25 2013]" and returns the category only
        '''
        category = ""
        startCat = catdue.find('[')
        if startCat == -1:
            category = catdue
        else:
           category = catdue[:startCat]
        return category

    def _getDueDateFromCatDue(self, catdue):
        '''
        Takes a "catdue" string (i.e., combination of category and due date,
        e.g., "Work [Mar 25 2013]" and returns the due date only
        '''
        duedate = ""
        startDueDate = catdue.find('[')
        if startDueDate == -1:
            duedate = _("No due date")
        else:
            duedate = catdue[startDueDate + 1 : catdue.find(']')]
        return duedate

    def complete_task(self, scope, uri):
        print "We have to complete this task: ", uri
        ids = self._getTaskIdsFromUri(uri)
        # TODO: uncomment
        #self._tasksInfoManager.markCompleted(self._rtm, ids['lid'], ids['tsid'], ids['tid'])
        # TODO force downloading new tasks
        # TODO: find a way to show the previous page!
        # http://developer.ubuntu.com/api/ubuntu-12.04/python/Unity-5.0.html#Unity.HandledType
        return Unity.ActivationResponse(handled = Unity.HandledType.GOTO_DASH_URI, goto_uri='unity.singlet.lens.tasks')

    def uncomplete_task(self, scope, uri):
        print "uncomplete"

if __name__ == "__main__":
    run_lens(TasksLens, sys.argv)
