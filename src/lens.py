#! /usr/bin/python

#    Copyright (c) 2013 Vincenzo Pii <vinc.pii@gmail.com>

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

# TODO: use logging system and remove prints
# TODO: package as app
# TODO: add logout button

from AuthManager import AuthManager
from ListsInfoManager import ListsInfoManager
from TasksDB import TasksDB
from TasksInfoManager import TasksInfoManager
from TokenManager import TokenManager
from datetime import datetime, timedelta
from gi.repository import GLib, Gio, GObject, Unity, Unity
from rtmapi import Rtm
from singlet.lens import SingleScopeLens, ListViewCategory
from singlet.utils import run_lens
from time import time, timezone, altzone, localtime
import gettext
import locale
import sys
import webbrowser

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
# String representing the ID for the show completed filter
SHOW_COMPLETED_FILTER_ID = "show_completed"

class TasksLens(SingleScopeLens):

    class Meta:
        name = 'tasks'
        title = _(u'Search Tasks').decode('utf-8')
        description = _(u'Tasks Search').decode('utf-8')
        search_hint = _(u'Search Tasks').decode('utf-8')
        icon = 'tasks.svg'
        category_order = ['tasks']
        filter_order = ['categoryFilter', 'displayedFieldsFilter', 'orderFilter', 'completedFilter']

    tasks = ListViewCategory(_(u"Tasks").decode('utf-8'), 'stock_yes')

    # id, display name, icon, contracted state
    categoryFilter = Unity.RadioOptionFilter.new("categoryFilter", _(u"Sections").decode('utf-8'), None, False)

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

    PRIORITIES = {'0': _(u'Oops, error!').decode('utf-8'),
                  '1': _(u'High Priority').decode('utf-8'),
                  '2': _(u'Medium Priority').decode('utf-8'),
                  '3': _(u'Low Priority').decode('utf-8'),
                  'N': _(u'Unspecified').decode('utf-8')}

    # Populate the category map
    for i in range(0, len(catNames)):
        categoryIdToNameMappingTable[str(i)] = catNames[i]

    # Populate the category filters
    if len(categoryIdToNameMappingTable) == 0:
        categoryFilter.add_option('0', _(u"Lens restart needed").decode('utf-8'), None)
    else:
        for i in range(0, len(categoryIdToNameMappingTable)):
            categoryFilter.add_option(categoryIdToNameMappingTable.keys()[i], categoryIdToNameMappingTable.values()[i], None)

    # Populate the ID filters
    displayedFieldsFilter = Unity.CheckOptionFilter.new("fieldsFilter", _(u"Fields to display").decode('utf-8'), None, False) 
    displayedFieldsFilter.add_option(CATEGORY_FIELD_FILTER_ID, _(u"Category").decode('utf-8'), None)
    displayedFieldsFilter.add_option(DUE_FIELD_FILTER_ID, _(u"Due").decode('utf-8'), None)
    displayedFieldsFilter.add_option(PRIORITY_FIELD_FILTER_ID, _(u"Priority").decode('utf-8'), None)

    # Populate the ordering filter
    orderFilter = Unity.RadioOptionFilter.new("orderingFilter", _(u"Sort by").decode('utf-8'), None, False)
    orderFilter.add_option(TasksInfoManager.ORDERING_PRIORITY_ID, _(u"Priority").decode('utf-8'), None)
    orderFilter.add_option(TasksInfoManager.ORDERING_DUE_ID, _(u"Due dates").decode('utf-8'), None)
    orderFilter.add_option(TasksInfoManager.ORDERING_NAMES_ID, _(u"Names").decode('utf-8'), None)

    # Filter for complete/uncomplete tasks
    completedFilter = Unity.RadioOptionFilter.new("completedFilter", _(u"Show/Hide").decode('utf-8'), None, False)
    completedFilter.add_option(SHOW_COMPLETED_FILTER_ID, _(u"Show completed tasks").decode('utf-8'), None)

    # Category visualization must be active by default
    displayedFieldsFilter.get_option(CATEGORY_FIELD_FILTER_ID).props.active = True
    displayedFieldsFilter.get_option(DUE_FIELD_FILTER_ID).props.active = True
    displayedFieldsFilter.get_option(PRIORITY_FIELD_FILTER_ID).props.active = True

    # Priority order as default
    orderFilter.get_option(TasksInfoManager.ORDERING_PRIORITY_ID).props.active = True

    # Do not show complete tasks as default
    completedFilter.get_option(SHOW_COMPLETED_FILTER_ID).props.active = False

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
        
        # Database
        self._db = TasksDB()
        
        # The user's current system timezone offset
        tzoffset = timezone if not localtime().tm_isdst else altzone
        self._tzoffset = timedelta(seconds = tzoffset * -1)

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
        self._tasksInfoManager.downloadTasksList(self._rtm, self._db)
        
        # Get the category to be displayed (if None, display them all)
        try:
            filteredCategoryId = self._scope.get_filter('categoryFilter').get_active_option().props.id
            filteredCategory = self.categoryIdToNameMappingTable[filteredCategoryId]
        except (AttributeError):
            filteredCategory = None
        except (KeyError):
            filteredCategory = None

        # Get the status of the show completed filter
        try:
            showCompleted = self._scope.get_filter('completedFilter').get_active_option().props.id
            showCompleted = True
        except (AttributeError):
            showCompleted = False

        # Get the lists of fields to be displayed for each task element
        optionalDisplayFields = []
        for option in self._scope.get_filter('fieldsFilter').options:
            if option.props.active == True:
                optionalDisplayFields.append(option.props.id)

        # Get the ordering, if any
        try:
            orderBy = self._scope.get_filter('orderingFilter').get_active_option().props.id
        except (AttributeError):
            orderBy = None
        
        # Filters at this point:
        # filteredCategoryId: id of the category (list id) to be displayed
        # orderBy: priority, due date or name
        # optionalDisplayFields:  contains elements of this set: ("category", "due", "priority")
        
        # get the tasks of the specified category (if not None), ordered on orderBy
        # and also completed tasks if required
        tasks = self._db.getTasks(filteredCategory, orderBy, showCompleted)

        for taskDictionary in tasks:
            categoryName = taskDictionary[TasksDB.TCATEGORY] if CATEGORY_FIELD_FILTER_ID in optionalDisplayFields else ""
            dueTime = self._prettyFormatDueDate(taskDictionary[TasksDB.TDUE]) if DUE_FIELD_FILTER_ID in optionalDisplayFields else ""
            priority = taskDictionary[TasksDB.TPRIORITY] if PRIORITY_FIELD_FILTER_ID in optionalDisplayFields else ""
            name = taskDictionary[TasksDB.TNAME]
            listId = taskDictionary[TasksDB.TLIST_ID]
            taskseriesId = taskDictionary[TasksDB.TSERIES_ID]
            taskId = taskDictionary[TasksDB.TID]
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
        # Download the tasks list
        self._tasksInfoManager.downloadTasksList(self._rtm, self._db)
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
        if current_task == last_task:
            # not found!! something very wrong happened
            raise ValueError('Unable to load task preview')
        taskInfo = self._db.getTaskById(identifiers['tid'], identifiers['lid'], identifiers['tsid'])
        # Title, description (not visible ?!), icon (set later)
        preview = Unity.GenericPreview.new(taskInfo[TasksDB.TCATEGORY], taskInfo[TasksDB.TNAME], None)
        icon = ICON + taskInfo[TasksDB.TPRIORITY] + ICON_EXTENSION
        preview.props.image_source_uri = icon
        icon = Gio.ThemedIcon.new(icon)
        preview.props.image = icon
        # Text
        preview.props.description_markup = self._getPreviewText(taskInfo[TasksDB.TCATEGORY], 
                                                                taskInfo[TasksDB.TDUE],
                                                                taskInfo[TasksDB.TPRIORITY],
                                                                taskInfo[TasksDB.TNAME],
                                                                taskInfo[TasksDB.TCOMPLETED])
        # add complete/uncomplete button
        if taskInfo[TasksDB.TCOMPLETED] is u'':
            # task has not been completed
            # description, string, icon
            view_action = Unity.PreviewAction.new('complete', _(u'Mark completed').decode('utf-8'), None)
            view_action.connect('activated', self.complete_task)
        else:
            view_action = Unity.PreviewAction.new('uncomplete', _(u'Mark uncompleted').decode('utf-8'), None)
            view_action.connect('activated', self.uncomplete_task)
        preview.add_action(view_action)
        return preview

    def _getPreviewText(self, category, due, priority, name, completed):
        '''
        Given task information returns the (formatted)
        text to be put in the preview screen for this task
        '''
        due = self._prettyFormatDueDate(due)
        s = u"<b>" + _(u"Category").decode('utf-8') + u"</b>: " +  category + u"\n"
        s += u"<b>" + _(u"Priority").decode('utf-8') + u"</b>: " + self.PRIORITIES[priority] + u"\n"
        s += u"<b>" + _(u"Due date") + u"</b>: " + due + u"\n"
        if completed is not u'':
            s += u"<b>" + _(u"Completed on").decode('utf-8') + u"</b>: " + self._prettyFormatDueDate(completed)  + u"\n"
        s += u"\n"
        s += u"<b>" + _(u"Description").decode('utf-8') + u"</b>\n"
        s += u"<i>{}</i>".format(name)
        return s

    def complete_task(self, scope, uri):
        print "Completing task...: ", uri
        ids = self._getTaskIdsFromUri(uri)
        self._tasksInfoManager.markCompleted(self._rtm, ids['lid'], ids['tsid'], ids['tid'])
        self._tasksInfoManager.refreshTasks()
        # http://developer.ubuntu.com/api/ubuntu-12.04/python/Unity-5.0.html#Unity.HandledType
        return Unity.ActivationResponse(handled = Unity.HandledType.SHOW_PREVIEW)#, goto_uri=uri)

    def uncomplete_task(self, scope, uri):
        print "Uncompleting task...: ", uri
        ids = self._getTaskIdsFromUri(uri)
        self._tasksInfoManager.markUncompleted(self._rtm, ids['lid'], ids['tsid'], ids['tid'])
        self._tasksInfoManager.refreshTasks()
        # http://developer.ubuntu.com/api/ubuntu-12.04/python/Unity-5.0.html#Unity.HandledType
        return Unity.ActivationResponse(handled = Unity.HandledType.SHOW_PREVIEW)
        
    def _prettyFormatDueDate(self, dueDateString):
        '''
        Parses the due date as provided by the service and
        produces a pretty representation
        '''
        if dueDateString == '':
            return ''

        # Input format example: 2012-03-29T22:00:00Z

        # Collect the tokens
        start = 0;
        firstHyphen = dueDateString.find('-')
        secondHyphen = dueDateString.rfind('-')
        bigT = dueDateString.find('T')
        firstColon = dueDateString.find(':')
        secondColon = dueDateString.rfind(':')
        bigZ =  dueDateString.find('Z')

        # Extract the strings
        year = dueDateString[start : firstHyphen]
        month = dueDateString[firstHyphen + 1 : secondHyphen]
        day = dueDateString[secondHyphen + 1 : bigT]
        hour = dueDateString[bigT + 1 : firstColon]
        minutes = dueDateString[firstColon + 1 : secondColon]
        seconds = dueDateString[secondColon + 1 : bigZ]

        # Build the formatted string
        dt = datetime (int(year), int(month), int(day), int(hour), int(minutes), int(seconds))
        dt = dt + self._tzoffset

        # E.g. 'Wed 07 Nov 2012 11:09AM'
        return dt.strftime("%a %d %b %Y %I:%M%p")

if __name__ == "__main__":
    run_lens(TasksLens, sys.argv)
