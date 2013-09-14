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

import webbrowser

class AuthManager(object):
    '''
    This class handles the RTM authentication process
    '''
    def __init__(self, icon, taskModelItem):
        super(AuthManager, self).__init__()

        # Authentication process state
        self._authReqPending = False

        # Icon to display
        self._icon = icon

        # Tasks model object for the model
        self._taskModelItem = taskModelItem

    def checkAndRequireAuthentication(self, rtmApi, model):
        if not self._isAuthNeeded(rtmApi):
            return False
        self._rtmRequireAuthentication(rtmApi, model)
        return True
    
    def _isAuthNeeded(self, rtmApi):
        if rtmApi.token_valid() and self._authReqPending == False:
            return False
        else:
            return True

    def _rtmRequireAuthentication(self, rtmApi, model):
        """
        Open the Web Browser to let the user authenticate
        """
        if self._authReqPending == True:
            self._displayAuthConfirmationRequest(model)
            return
        self._displayAuthConfirmationRequest(model)
        # use desktop-type authentication
        url, self.frob = rtmApi.authenticate_desktop()
        # open webbrowser, wait until user authorized application
        webbrowser.open(url)
        self._authReqPending = True

    def _displayAuthConfirmationRequest(self, model):
        """
        Displays an item to inform the user how to authenticate with the online
        RTM service
        """
        model.append('rtmLens://auth/wait',
            self._icon,
            self._taskModelItem,
            'text/plain',
            _('Authorization required').decode('utf-8'),
            _('Check your web browser. Click this icon when finished.').decode('utf-8'),
            '')

    def rtmCompleteAuthentication(self, rtmApi, tokenManager):
        """
        Callback method invoked when the user clicks
        the authentication button to confirm it
        """
        # Get the token for the frob
        rtmApi.retrieve_token(self.frob)
        # Store the token
        token = rtmApi.token
        # Signal that the auth process has finished
        self._authReqPending = False

        # If the token is valid, store it to a file
        if token is not None:
            tokenManager.saveTokenToFile(token)
        return token

