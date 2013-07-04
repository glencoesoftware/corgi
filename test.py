#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

:author: Sam Hart <sam@glencoesoftware.com>

Test for Corgi
Copyright (c) 2007, Glencoe Software, Inc.
See LICENSE for details.

"""

from corgi import Corgi

import sys

if len(sys.argv) != 4:
	# So stupid that we dont even use parser!
	print "Simple test for Corgi\n"

	print "Usage:"
	print "  test.py URL AUTHKEY ISSUE_ID\n"
	print "Where:"
	print "\tURL\t\tThe Redmine URL"
	print "\tAUTHKEY\t\tThe Redmine user's authkey"
	print "\tISSUE_ID\t\tThe issue id to update"
	sys.exit(1)
else:
	url = sys.argv[1]
	authkey = sys.argv[2]
	issueid = sys.argv[3]

	c = Corgi(url, authkey)
	if c.connected:
		print "Connected to %s" % url
		print "==="
		print "Please enter text to add to the issue as a comment:"
		text = raw_input("-> ")
		c.updateIssue(issueid, text)
		print "\nCheck that the comment has been added..."
