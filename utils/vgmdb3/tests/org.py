# -*- coding: UTF-8 -*-
import os
import unittest

from vgmdb.parsers import org

base = os.path.dirname(__file__)

class TestOrgs(unittest.TestCase):
	def setUp(self):
		pass

	def test_dogear(self):
		dogear_code = file(os.path.join(base, 'org_dogear.html'), 'r').read()
		dogear = org.parse_page(dogear_code)
		self.assertEqual("Dog Ear Records Co., Ltd.", dogear['name'])
		self.assertEqual("Label / Imprint", dogear['type'])
		self.assertEqual("Japan", dogear['region'])
		self.assertEqual("Nobuo Uematsu", dogear['staff'][0]['names']['en'])
		self.assertEqual("Miyu", dogear['staff'][1]['names']['en'])
		self.assertEqual(True, dogear['staff'][0]['owner'])
		self.assertEqual(2, len(dogear['staff']))
		self.assertEqual("No description available", dogear['description'])
		self.assertEqual(28, len(dogear['releases']))
		self.assertEqual("DERP-10001", dogear['releases'][0]['catalog'])
		self.assertEqual("album/5343", dogear['releases'][0]['link'])
		self.assertEqual("Kalaycilar", dogear['releases'][2]['titles']['en'])
		self.assertEqual("2008-03-19", dogear['releases'][1]['date'])
		self.assertEqual("Publisher", dogear['releases'][1]['role'])
		self.assertEqual(True, dogear['releases'][19]['reprint'])
		self.assertEqual("https://vgmdb.net/db/assets/logos-medium/135-1246205463.gif", dogear['picture_small'])
		self.assertEqual("https://vgmdb.net/db/assets/logos/135-1246205463.gif", dogear['picture_full'])

	def test_vagrancy(self):
		vagrancy_code = file(os.path.join(base, 'org_vagrancy.html'), 'r').read()
		vagrancy = org.parse_page(vagrancy_code)
		self.assertEqual("VAGRANCY", vagrancy['name'])
		self.assertEqual("Akiko Shikata", vagrancy['staff'][0]['names']['en'])
		self.assertEqual("志方あきこ", vagrancy['staff'][0]['names']['ja'])
		self.assertEqual("2012-11", vagrancy['releases'][-2]['date'])
		self.assertEqual("Comic Market 67", vagrancy['releases'][4]['event']['name'])
		self.assertEqual("event/15", vagrancy['releases'][4]['event']['link'])


if __name__ == '__main__':
	unittest.main()
