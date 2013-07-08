#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

:author: Sam Hart <sam@glencoesoftware.com>

Test for Corgi
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
		c.update_issue(issueid, text)
		print "\nCheck that the comment has been added..."
