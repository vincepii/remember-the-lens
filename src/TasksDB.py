#! /usr/bin/python

#    Copyright (c) 2013 Vincenzo Pii <vinc.pii@gmail.com>

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version, with the following additional
#    restriction: 
#    you cannot modify or redistribute this software if you don't use your
#    own Remember The Milk API Key and Shared Secret pair, or receive explicit
#    permission from the author (<vinc.pii@gmail.com>) to include your
#    changes to the code.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

#    This product uses the Remember The Milk API but is not endorsed or
#    certified by Remember The Milk.

import sqlite3

class TasksDB(object):
    """
    This class is a wrapper for an SqLite database in which to store
    information about tasks.
    
    It implements a context manager, so it can be used as:
    with TasksDB as db:
        # usage
    """

    TASKS_TABLE_NAME = 'tasks'
    LISTS_TABLE_NAME = 'lists'
    
    # List of keys to dictionaries describing a task, for easy access by external modules
    TNAME = "name"
    TLIST_ID = TASKS_TABLE_NAME + ".listid"
    TSERIES_ID = "taskseriesid"
    TID = "taskid"
    TDUE = "due"
    TPRIORITY = "priority"
    TCOMPLETED = "completed"
    TCATEGORY = "listname"
    

    def __init__(self):
        super(TasksDB, self).__init__()
        
        self.NAMED_DB = 'memorydb'
        
        # Connection to SqLite DB
        self._dbconn = None
        
        # Keys to dictionaries describing tasks returned when the DB is queried
        # If a new item must be returned for a task, just add the corresponding
        # column DB name to this list
        # e.g.: this will only get task name and id: self.columns = [self.TID, self.TNAME]
        self.columns = [self.TLIST_ID, self.TSERIES_ID, self.TID, self.TNAME, self.TDUE, self.TPRIORITY, self.TCOMPLETED, self.TCATEGORY]

        # In memory database with a name so it can be shared
        self._dbconn = sqlite3.connect(':memory:')
        self._createTasksTable()
        self._createListsTable()

    def close(self, exc_type, exc_info, exc_tb):
        self._dbconn.close()

    def _createTasksTable(self):
        '''
        Creates the table to store the tasks
        '''
        cursor = self._dbconn.cursor()
        # list-id, task-series-id and task-id are a primary key
        cursor.execute('''create table ''' + self.TASKS_TABLE_NAME +
        ''' (listid    text,
        taskseriesid   text,
        taskid         text,
        completed      text,
        name           text,
        due            text,
        priority       text)
        ''')

    def _createListsTable(self):
        '''
        Creates the table to store information about lists: mapping between
        list id and list name
        '''
        cursor = self._dbconn.cursor()
        cursor.execute('''CREATE TABLE ''' + self.LISTS_TABLE_NAME +
        '''(listid text,
        listname   text)
        ''')

    def _cleanDatabaseEntries(self, tableName):
        '''
        Deletes every row of the databases
        '''
        cursor = self._dbconn.cursor()
        cursor.execute('delete from ' + tableName)

    def storeTasks(self, taskLists):
        '''
        This method will parse the xml based representation of tasks as
        provided by the RTM apis (see 
        http://www.rememberthemilk.com/services/api/methods/rtm.tasks.getList.rtm)
        and store data in SqLite.
        '''
        # delete the whole database as we received fresh information
        self._cleanDatabaseEntries(self.TASKS_TABLE_NAME)
        cursor = self._dbconn.cursor()
        # iterate over the elements and populate database
        for taskList in taskLists.tasks:
            for taskseries in taskList:
                row = [taskList.id,
                       taskseries.id,
                       taskseries.task.id,
                       taskseries.task.completed,
                       taskseries.name,
                       taskseries.task.due,
                       taskseries.task.priority]
                cursor.execute('insert into ' + self.TASKS_TABLE_NAME + ' values (?,?,?,?,?,?,?)', row)

    def storeLists(self, lists):
        '''
        Parses the XML representation of lists and populates the LISTS database
        '''
        # delete the whole database as we received fresh information
        self._cleanDatabaseEntries(self.LISTS_TABLE_NAME)
        cursor = self._dbconn.cursor()
        # iterate over the elements and populate database
        for entry in lists.lists:
            row = [entry.id, entry.name]
            cursor.execute('insert into ' + self.LISTS_TABLE_NAME + ' values (?,?)', row)

    def dumpTasks(self):
        cursor = self._dbconn.cursor()
        output = cursor.execute('select * from ' + self.TASKS_TABLE_NAME)
        return output
    
    def getTasks(self, categoryName, orderBy, showCompleted):
        '''
        Given the string name of a category, returns all the tasks
        belonging to that category, ordered on the specified column (if not
        None) and also providing uncompleted tasks if showCompleted is True.
        
        Return type is a list of dictionaries, one for each task.
        E.g.: [{'taskseriesid': u'xxx', 'name': u'xxx', 'due': u'', 
                'priority': u'N', 'listid': u'xxx', 'taskid': u'xxx'},
               {'taskseriesid': u'xxx', 'name': u'xxx', 'due': u'',
                'priority': u'N', 'listid': u'xxx', 'taskid': u'xxx'}]
        '''
        
        cursor = self._dbconn.cursor()
        
        category_where = ''
        if categoryName is not None:
            category_where = " and listname=\'" + categoryName + "\'"

        # Order by statement
        if orderBy is not None:
            orderByStm = ' ORDER BY ' + orderBy
        else:
            orderByStm = ""

        if showCompleted is True:
            # will show completed and uncompleted tasks
            completedStm = ""
        else:
            # only uncompleted tasks
            completedStm = " and completed=\'\' "

        # Get all the specified columns from DB
        select = 'select ' + (', ').join(self.columns)
        tasks = cursor.execute(select + 
                    ' from ' + self.TASKS_TABLE_NAME + ' as tasks, ' + 
                    self.LISTS_TABLE_NAME + ' as lists ' +
                    ' where tasks.listid = lists.listid' + completedStm +
                    category_where + 
                    orderByStm)
        
        # prepare a dictionary to return the tasks
        ldic = []
        for row in tasks:
            d = {}
            for index, column in enumerate(self.columns):
                d[column] = row[index]
            ldic.append(d)
        
        return ldic
    
    def getTaskById(self, taskId, listId, taskSeriesId):
        '''
        Given a list id, task id and task series id, returns a dictionary
        describing the task
        '''
        cursor = self._dbconn.cursor()
        select = "select " + (", ").join(self.columns)
        task = cursor.execute(select + " from " + self.TASKS_TABLE_NAME + " as tasks, " +
               self.LISTS_TABLE_NAME + " as lists "
               " where tasks.listid = lists.listid and "
               " tasks.listid=(?) and tasks.taskseriesid=(?) and "
               " tasks.taskid=(?)", (listId, taskSeriesId, taskId))
        
        row = cursor.fetchone()
        if row is None:
            raise ValueError('Cannot find any task with given identifiers. task id: {} list id: {} task series id: {}'.format(taskId, listId, taskSeriesId))
        
        d = {}
        for index, column in enumerate(self.columns):
            d[column] = row[index]
        
        return d
