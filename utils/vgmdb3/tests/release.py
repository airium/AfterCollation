# -*- coding: UTF-8 -*-
import os
import unittest

from vgmdb.parsers import release

base = os.path.dirname(__file__)

class TestReleases(unittest.TestCase):
	def setUp(self):
		pass

	def test_ataraxiavita(self):
		at_code = file(os.path.join(base, 'release_hollowataraxiavita.html'), 'r').read()
		at = release.parse_page(at_code)
		self.assertEqual('Fate/hollow ataraxia', at['name'])
		self.assertEqual('Fate/hollow ataraxia', at['products'][0]['names']['en'])
		self.assertEqual('product/2029', at['products'][0]['link'])
		self.assertEqual('VLJM-35123', at['catalog'])
		self.assertEqual('4997766201689', at['upc'])
		self.assertEqual('2014-11-27', at['release_date'])
		self.assertEqual('Official Release', at['release_type'])
		self.assertEqual('Sony PlayStation Vita', at['platform'])
		self.assertEqual('JPY (Japan)', at['region'])
		self.assertEqual(2, len(at['release_albums']))
		self.assertEqual(25, len(at['product_albums']))
		self.assertEqual('broKen NIGHT / Aimer', at['release_albums'][0]['titles']['en'])
		self.assertEqual('DFCL-2100', at['release_albums'][0]['catalog'])
		self.assertEqual(['Vocal', 'OP/ED/Insert'], at['release_albums'][0]['classifications'])
		self.assertEqual('album/48061', at['release_albums'][0]['link'])
		self.assertEqual('game', at['release_albums'][0]['type'])
		self.assertEqual('2014-12-17', at['release_albums'][0]['date'])
		self.assertEqual('TYPE-MOON Fes. Drama CD', at['product_albums'][-2]['titles']['en'])
		self.assertEqual('ANZX-6458', at['product_albums'][-2]['catalog'])
		self.assertEqual(['Drama'], at['product_albums'][-2]['classifications'])
		self.assertEqual('album/37706', at['product_albums'][-2]['link'])
		self.assertEqual('bonus', at['product_albums'][-2]['type'])
		self.assertEqual('2013-01-16', at['product_albums'][-2]['date'])
		self.assertEqual('2014-09-13T08:01', at['meta']['added_date'])
		self.assertEqual('2014-09-13T08:01', at['meta']['edited_date'])
		self.assertEqual(112, at['meta']['visitors'])

	def test_ataraxiapc(self):
		at_code = file(os.path.join(base, 'release_hollowataraxiapc.html'), 'r').read()
		at = release.parse_page(at_code)
		self.assertEqual(0, len(at['release_albums']))	# this release doesn't have albums
		self.assertEqual(25, len(at['product_albums']))
		self.assertEqual('ANZX-6458', at['product_albums'][-2]['catalog'])
		self.assertEqual(['Drama'], at['product_albums'][-2]['classifications'])
		self.assertEqual('album/37706', at['product_albums'][-2]['link'])
		self.assertEqual('bonus', at['product_albums'][-2]['type'])
		self.assertEqual('2013-01-16', at['product_albums'][-2]['date'])

if __name__ == '__main__':
	unittest.main()
