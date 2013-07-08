# -*- coding: utf-8 -*-

"""

:author: Sam Hart <sam@glencoesoftware.com>

Glue between Github issues and Redmine
Copyright (C) 2013 Glencoe Software, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import logging, copy

from redmine import Redmine

logger = logging.getLogger('corgi')

class RedmineServerUnset(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr("Redmine server information unset- %s" % self.value)

class RedmineServerAlreadySet(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr("Redmine server information has already been set- %s" \
            % self.value)

class RedmineAlreadyConnected(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class RedmineNotConnected(Exception):

    def __init__(self, value=""):
        self.value = value

    def __str__(self):
        return repr("Not connected to Redmine server- %s" % self.value)

class Corgi(object):
    """
    Simple interaction with a Redmine server.

    By placing this in its own class, we can abstract out the underlying
    operations and remove the dependency on pyredmine and dateutil if we
    ever want to.
    """

    def __init__(self, serverURL = None, authKey = None, impersonate=None):
        """
        Constructor which takes the URL for the Redmine server and
        associated user authentication key. Will set up the instance
        for future interactions.

        If serverURL or authKey are omitted, no connection will be
        established, and you will have to call connect() yourself.
        """
        self.connected = False
        self._serverURL = None
        self._authKey = None
        self._redmine = None
        self._impersonate = impersonate

        if serverURL:
            self.set_server_url(serverURL)

        if authKey:
            self.set_auth_key(authKey)

        try:
            self.connect()
        except RedmineServerUnset:
            logger.info('Not connected to Redmine.')

    def set_server_url(self, serverURL):
        """
        If serverURL is not set, will set it. Otherwise will raise the
        RedmineServerAlreadySet exception.

        If you wish to connect to a different server, do not attempt to
        change the serverURL. Instead, create a new instance of the Corgi
        class.
        """
        if self._serverURL is None:
            self._serverURL = str(serverURL)
        else:
            raise RedmineServerAlreadySet("Server URL has already been set.")

    def get_server_url(self):
        return copy.copy(self._serverURL)

    def set_auth_key(self, authkey):
        """
        If the authentication key is not set, will set it. Otherwise will raise
        the RedmineServerAlreadySet exception.

        If you wish to change the authentication key, do not attempt to call
        this method again. Instead, delete the old instance of Corgi and make
        a new one.
        """
        if self._authKey is None:
            self._authKey = str(authkey)
        else:
            raise RedmineServerAlreadySet(\
                "Authentication key already set.")

    def get_auth_key(self):
        return copy.copy(self._authKey)

    def connect(self):
        """
        If not connected, will attempt to connect with the Redmine server. If
        we are already connected, will raise the RedmineAlreadyConnected
        exception.

        If the server information has not been set, will raise the
        RedmineServerUnset exception.
        """
        if not self.connected:
            if self._serverURL is not None and self._authKey is not None:
                self._redmine = Redmine(self._serverURL, self._authKey,
                                        impersonate=self._impersonate)
                self.connected = True
            else:
                raise RedmineServerUnset(\
                    'Please set server URL and authentication key.')
        else:
            raise RedmineAlreadyConnected("Already connected to %s" % \
                self._serverURL)

    def new_issue(self, project, subject, description):
        """
        Creates a new issue in project with the subject and description.

        Returns the new issue's id on success.

        FIXME: Would be nice if we could do more than just subject and
        description. Need error checking.
        """
        if self.connected:
            p = self._redmine.projects['project']
            issue = p.issues.new(subject = subject, description = description)
            return issue.id
        else:
            raise RedmineNotConnected()

    def update_issue(self, issueId, update, statusId=None):
        """
        Updates an existing issue denoted by issueId. The update contains
        the comments to add. If a statusId is provided, it will be used,
        otherwise the existing statusId will be used.

        FIXME: Very 'meh' now. Need error checking. statusId assumes the
        caller 'knows what they are doing' and will match what's in redmine-
        a risky assumption.
        """
        if self.connected:
            issue = self._redmine.issues[issueId]
            if statusId is None:
                statusId = int(issue.status)
            issue.set_status(statusId, update)
            # XXX May want to queue these up and have a final commit?
            issue.save()
        else:
            raise RedmineNotConnected()

    def get_issue_title(self, issueId):
        """
        Retrieve the title for a given issue
        """
        if self.connected:
            issue = self._redmine.issues[issueId]
            return issue.subject
        else:
            raise RedmineNotConnected()
