#! /usr/bin/python

#    Copyright (c) 2011 Vincenzo Pii <vinc.pii@gmail.com>

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


from time import time

class TasksInfoManager(object):
    '''
    This class describes the Remember The Milk tasks
    '''

    class TaskDescriptor:
        '''
        Class to describe a single task
        '''
        def __init__(self):
            # Task category, e.g. "Personal"
            self.category = ""
            # Task name: its description, e.g. "Remember The Milk"
            self.name = ""
            # Due time
            self.due = ""
            # Priority
            self.priority = ""

    # Time interval to consider the tasksList cache old (in seconds)
    TASKS_LIST_UPDATE_INTERVAL = 20

    def __init__(self, listsManager):
        super(TasksInfoManager, self).__init__()
        
        # RTM Tasks XML representation
        # See http://www.rememberthemilk.com/services/api/methods/rtm.tasks.getList.rtm
        self._tasksList = None

        # The timestamp associated with the tasks list
        self._tasksListTimestamp = 0
        
        # Reference to the lists manager object
        self._listsManager = listsManager

    def getTasksOfCategory(self, categoryName):
        '''
        Given a category name, returns a list of tasks
        belonging to that category.
        Return type: list of <taskDescriptor>
        '''
        tasks = []

        # Get the corresponding id
        try:
            categoryId = self._listsManager.getListId(categoryName)
        except KeyError:
            categoryId = 0

        # Return tasks of every category
        for taskList in self._tasksList.tasks:
            if categoryId != 0 and taskList.id != categoryId: 
                # Skip this item
                continue
            # Get the tasks of this category
            for taskseries in taskList:
                descriptor = TasksInfoManager.TaskDescriptor()
                descriptor.category = self._listsManager.getListName(taskList.id) 
                descriptor.name = taskseries.name
                descriptor.due = taskseries.task.due
                descriptor.priority = taskseries.task.priority
                tasks.append(descriptor)
        return tasks

    def downloadTasksList(self, rtmApi):
        '''
        Downloads the tasks from RTM if the cached list is empty or too old
        '''
        if self._tasksList == None or self._tasksListExpired() == True:
            # get all open tasks, see http://www.rememberthemilk.com/services/api/methods/rtm.tasks.getList.rtm
            self._tasksList = rtmApi.rtm.tasks.getList(filter="status:incomplete")

            # Builds the lists information
            self._listsManager.buildTheListsDictionary(rtmApi)
            
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

