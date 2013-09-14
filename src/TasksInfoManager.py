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


from time import time, timezone, altzone, localtime
from datetime import datetime, timedelta
from TasksDB import TasksDB

class TasksInfoManager(object):
    '''
    This class describes the Remember The Milk tasks
    '''

    # Time interval to consider the tasksList cache old (in seconds)
    TASKS_LIST_UPDATE_INTERVAL = 20

    # String representing the ID for the priority ordering filter
    ORDERING_PRIORITY_ID = TasksDB.TPRIORITY
    # String representing the ID for the due date ordering filter
    ORDERING_DUE_ID = TasksDB.TDUE
    # String representing the ID for the due date ordering filter
    ORDERING_NAMES_ID = TasksDB.TNAME

    def __init__(self, listsManager):
        super(TasksInfoManager, self).__init__()
        
        # RTM Tasks XML representation
        # See http://www.rememberthemilk.com/services/api/methods/rtm.tasks.getList.rtm
        self._tasksList = None

        # The timestamp associated with the tasks list
        self._tasksListTimestamp = 0
        
        # Reference to the lists manager object
        self._listsManager = listsManager
        
        # The user's current system timezone offset
        tzoffset = timezone if not localtime().tm_isdst else altzone
        self._tzoffset = timedelta(seconds = tzoffset * -1)

    def downloadTasksList(self, rtmApi, db):
        '''
        Downloads the tasks from RTM if the cached list is empty or too old
        '''
        if self._tasksList == None or self._tasksListExpired() == True:
            # get all open tasks, see http://www.rememberthemilk.com/services/api/methods/rtm.tasks.getList.rtm
            #self._tasksList = rtmApi.rtm.tasks.getList(filter="status:incomplete")
            self._tasksList = rtmApi.rtm.tasks.getList()
            
            # Store tasks in database
            db.storeTasks(self._tasksList)
            
            # Get the lists, see http://www.rememberthemilk.com/services/api/methods/rtm.lists.getList.rtm
            lists = rtmApi.rtm.lists.getList()
            
            db.storeLists(lists)
            
            # update the local cache timestamp
            self._tasksListTimestamp = self._now()

    def _tasksListExpired(self):
        """
        Returns True if the local tasksList is expired
        """
        if self._now() - self._tasksListTimestamp > self.TASKS_LIST_UPDATE_INTERVAL:
            return True
        else:
            return False

    def _now(self):
        """
        Returns the current time in seconds since the epoch
        """
        return int(time())

    def markCompleted(self, rtmApi, listId, taskSeriesId, taskId):
        '''
        Mark the task identified by the given IDs as completed.
        '''
        # The operation requires a timeline
        result = rtmApi.rtm.timelines.create()
        timeline = result.timeline.value
        # Complete task
        rtmApi.rtm.tasks.complete(timeline = timeline,
                                  list_id = listId,
                                  taskseries_id = taskSeriesId,
                                  task_id = taskId)

    def markUncompleted(self, rtmApi, listId, taskSeriesId, taskId):
        '''
        Mark the task identified by the given IDs as not completed.
        '''
        # The operation requires a timeline
        result = rtmApi.rtm.timelines.create()
        timeline = result.timeline.value
        # Uncomplete task
        rtmApi.rtm.tasks.uncomplete(timeline = timeline,
                                  list_id = listId,
                                  taskseries_id = taskSeriesId,
                                  task_id = taskId)

    def refreshTasks(self):
        '''
        Task list will be downloaded again on next update, despite the
        timestamp
        '''
        # Invalidate the timestamp so the list of tasks will be
        # downloaded again
        self._tasksListTimestamp = 0;

