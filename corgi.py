import logging

from redmine import Redmine

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


class Corgi:
	"""
	Simple interaction with a Redmine server.
	"""

	def __init__(self, serverURL = None, authkey = None):
		"""
		Constructor which takes the URL for the Redmine server and
		associated user authentication key. Will set up the instance
		for future interactions.

		If serverURL or authKey are omitted, no connection will be
		established, and you will have to call connect() yourself.
		"""
		self.logger = logging.getLogger('Corgi')
		self.connected = False
		self._serverURL = None
		self._authKey = None
		self._redmine = None

		if serverURL:
			self.setServerURL(serverURL)

		if authKey:
			self.setAuthKey(authkey)

		try:
			self.connect()
		except RedmineServerUnset:
			self.logger.info('Not connected to Redmine.')

	def setServerURL(self, serverURL):
		"""
		If serverURL is not set, will set it. Otherwise will raise the
		RedmineServerAlreadySet exception.

		If you wish to connect to a different server, do not attempt to
		change the serverURL. Instead, create a new instance of the Corgi
		class.
		"""
		if self._serverURL == None:
			self._serverURL = str(serverURL)
		else:
			raise RedmineServerAlreadySet("Server URL has already been set.")

	def setAuthKey(authkey):
		"""
		If the authentication key is not set, will set it. Otherwise will raise
		the RedmineServerAlreadySet exception.

		If you wish to change the authentication key, do not attempt to call
		this method again. Instead, delete the old instance of Corgi and make
		a new one.
		"""
		if self._authKey == None:
			self._authKey = str(authkey)
		else:
			raise RedmineServerAlreadySet(\
				"Authentication key already set.")

	def connect(self):
		"""
		If not connected, will attempt to connect with the Redmine server. If
		we are already connected, will raise the RedmineAlreadyConnected
		exception.

		If the server information has not been set, will raise the
		RedmineServerUnset exception.
		"""
		if not self.connected:
			if self._serverURL != None and self._authKey != None:
				self._redmine = Redmine(self._serverURL, self._authKey)
				self.connected = True
			else:
				raise RedmineServerUnset(\
					'Please set server URL and authentication key.')
		else:
			raise RedmineAlreadyConnected("Already connected to %s" % \
				self._serverURL)

