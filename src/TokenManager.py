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


import os

class TokenManager(object):

    TOKEN_FILE = os.getenv('HOME') + "/.config/remember-the-lens/token"

    def __init__(self):
        super(TokenManager, self).__init__()

    def saveTokenToFile(self, token):
        tokenFileFullPath = os.path.expanduser(self.TOKEN_FILE)
        tokenFileFolders = tokenFileFullPath[0:tokenFileFullPath.rfind('/')]
        if not os.path.exists(tokenFileFolders):
            os.makedirs(tokenFileFolders)

        f = open(tokenFileFullPath, 'w+')
        f.write(token)
        f.close()

    def readTokenFromFile(self):
        try:
            f = open(os.path.expanduser(self.TOKEN_FILE))
        except IOError:
            return None
        token = f.read()
        return token

