# -*- coding: UTF-8 -*-
import os
import unittest

from vgmdb.parsers import event

base = os.path.dirname(__file__)

class TestEvents(unittest.TestCase):
	def setUp(self):
		pass

	def test_m3(self):
		m3_code = file(os.path.join(base, 'event_m3.html'), 'r').read()
		m3 = event.parse_page(m3_code)
		self.assertEqual('M3-2012 Fall', m3['name'])
		self.assertEqual('2012-10-28', m3['startdate'])
		self.assertEqual('2012-10-28', m3['enddate'])
		self.assertEqual('New Release', m3['releases'][0]['release_type'])
		self.assertEqual('works', m3['releases'][0]['album_type'])
		self.assertEqual('DVSP-0084', m3['releases'][3]['catalog'])
		self.assertEqual('AD:TECHNO', m3['releases'][4]['titles']['en'])
		self.assertEqual('Clinochlore', m3['releases'][2]['publisher']['names']['en'])
		self.assertEqual('Diverse System', m3['releases'][3]['publisher']['names']['en'])
		self.assertEqual('org/331', m3['releases'][3]['publisher']['link'])
		self.assertEqual('2012-10-28', m3['releases'][5]['release_date'])
		self.assertEqual(30, len(m3['releases']))

	def test_cm54(self):
		cm54_code = file(os.path.join(base, 'event_cm54.html'), 'r').read()
		cm54 = event.parse_page(cm54_code)
		self.assertEqual('Comic Market 54', cm54['name'])
		self.assertEqual('1998-08-14', cm54['startdate'])
		self.assertEqual('1998-08-16', cm54['enddate'])
		self.assertEqual(8, len(cm54['releases']))


if __name__ == '__main__':
	unittest.main()
