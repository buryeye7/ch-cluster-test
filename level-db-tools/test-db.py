#!/usr/bin/python
#-*-coding: utf-8-*-

import plyvel

db = plyvel.DB('tests', create_if_missing=True)
db.put('감사', 'value')

for key, value in db:
	print(key)
	#print(key, value)
