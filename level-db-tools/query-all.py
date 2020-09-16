#!/usr/bin/python

import plyvel
db = plyvel.DB('/home/opc/.gaiad/data/application.db')

for key, value in db:
	print 'key: ' + key
	print 'value: ' + value
