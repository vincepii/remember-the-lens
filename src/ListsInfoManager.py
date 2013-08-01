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


from rtmapi import Rtm

from TokenManager import TokenManager

class ListsInfoManager(object):
    '''
    This class retrieves lists information from the RTM service.

    It has the following responsibilities:
        * Provide the <listid, listname> mappings
        * Provide the list of listnames in a static manner
    '''

    def __init__(self):
        super(ListsInfoManager, self).__init__()

        # Object to translate from list id to list name
        # eg: <20897252, Study>
        self._listsDictionary = {}

        # Object to translate from list name to list id
        self._reverseListsDictionary = {}

        # Full representation of the RTM lists xml object
        self._rtmListsRepresentation = None

    def _getTheRtmListsRepresentation(self, rtmApi):
        '''
        Queries the RTM service to get the lists xml representation 
        '''
        if self._rtmListsRepresentation != None:
            return
        # Get the lists, see http://www.rememberthemilk.com/services/api/methods/rtm.lists.getList.rtm
        self._rtmListsRepresentation = rtmApi.rtm.lists.getList()
    
    def buildTheListsDictionary(self, rtmApi):
        '''
        This method downloads the lists information from the RTM service
        and builds the <listId, listName> dictionary
        '''
        self._getTheRtmListsRepresentation(rtmApi)
        # build the internal representation of categories
        for element in self._rtmListsRepresentation.lists:
            self._listsDictionary[element.id] = element.name
            self._reverseListsDictionary[element.name] = element.id

    def getListName(self, listId):
        '''
        Given a list listId, returns the list name
        '''
        try:
            name = self._listsDictionary[listId]
        except KeyError:
            print "Unknown list listId"
        return name

    def getListId(self, listName):
        '''
        Given a list name, returns its listId
        '''
        try:
            listId = self._reverseListsDictionary[listName]
        except KeyError:
            raise KeyError
        return listId

    def getTaskByName(self, listId, name, rtmApi):
        '''
        Given a list id and a task name (the task description), returns
        an XML representation of that list filtered with that task name

        http://www.rememberthemilk.com/services/api/methods/rtm.tasks.getList.rtm
        '''
        uname = name.decode("utf-8")
        return rtmApi.rtm.tasks.getList(list_id = listId, filter=u'name:{}'.format(uname))

    @staticmethod
    def getTheCategoriesListStatically(apiKey, sharedSecret):
        '''
        This method uses the RTM service by instantiating a new RTM object
        and tries to retrieve the list of listnames from the service.
        It can be run independently, as it uses an extra instance of the
        RTM object
        '''
        listsNames = []
        tokenManager = TokenManager()
        token = tokenManager.readTokenFromFile()
        if (token is None):
            # If the token doesn't exist, it won't work
            return listsNames
        rtm = Rtm(apiKey, sharedSecret, "read", token)
        if not rtm.token_valid():
            # The token wasn't vaid
            return listsNames
        # Get the lists description, see http://www.rememberthemilk.com/services/api/methods/rtm.lists.getList.rtm
        listsList = rtm.rtm.lists.getList()
        # Get the name of each list
        for element in listsList.lists:
            listsNames.append(element.name)
        return listsNames

