# -*- coding: UTF-8 -*-
import os
import unittest

import vgmdb.parsers.search

base = os.path.dirname(__file__)

class TestSearchList(unittest.TestCase):
	def setUp(self):
		pass

	def test_search(self):
		search_code = file(os.path.join(base, 'search.html'), 'r').read()
		search = vgmdb.parsers.search.parse_page(search_code)

		self.assertEqual(8, len(search['results']['albums']))
		self.assertEqual(1, len(search['results']['artists']))
		self.assertEqual(1, len(search['results']['orgs']))
		self.assertEqual(1, len(search['results']['products']))
		self.assertEqual("vagran", search['query'])
		self.assertEqual("album/71068", search['results']['albums'][0]['link'])
		self.assertEqual("Vagrant Story Original Soundtrack", search['results']['albums'][1]['titles']['en'])
		self.assertEqual("MICA-0368~9", search['results']['albums'][2]['catalog'])
		self.assertEqual("2000", search['results']['albums'][1]['release_date'])
		self.assertEqual("2003-12-28", search['results']['albums'][4]['release_date'])
		self.assertEqual("Samuel Day", search['results']['artists'][0]['names']['en'])
		self.assertEqual("The Vagrance", search['results']['artists'][0]['aliases'][0])
		self.assertEqual("VAGRANCY", search['results']['orgs'][0]['names']['en'])
		self.assertEqual("Vagrant Story", search['results']['products'][0]['names']['en'])
		self.assertEqual("ベイグラントストーリー", search['results']['products'][0]['names']['ja'])
		self.assertEqual("Vagrant Story", search['results']['products'][0]['names']['ja-latn'])
		self.assertEqual("Game", search['results']['products'][0]['type'])

	def test_search_quotes(self):
		search_code = file(os.path.join(base, 'search_quotes.html'), 'r').read()
		search = vgmdb.parsers.search.parse_page(search_code)

		self.assertEqual("''Snake Eater'' song from METAL GEAR SOLID 3", search['query'])


if __name__ == '__main__':
	unittest.main()
