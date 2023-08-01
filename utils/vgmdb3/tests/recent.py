# -*- coding: UTF-8 -*-
import os
import unittest

from vgmdb.parsers import recent

base = os.path.dirname(__file__)

class TestRecent(unittest.TestCase):
	def setUp(self):
		pass

	def test_albums(self):
		html = file(os.path.join(base, 'recent_albums.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-20T15:40', data['meta']['edited_date'])
		self.assertEqual('albums', data['section'])

		self.assertTrue(up[0]['deleted'])
		self.assertTrue(up[1]['deleted'])
		self.assertEqual('deleted', up[0]['edit'])
		self.assertEqual('Deleted/Inactive Album', up[0]['titles']['en'])
		self.assertEqual('rejected', up[1]['edit'])
		self.assertEqual('東方人 -TOHO BEAT-', up[1]['titles']['ja'])
		self.assertEqual('new', up[5]['edit'])
		self.assertTrue('new' in up[5])
		self.assertFalse('catalog' in up[0])
		self.assertEqual('N/A', up[2]['catalog'])
		self.assertEqual('album/42368', up[2]['link'])
		self.assertEqual('2013-08-12', up[2]['release_date'])
		self.assertEqual('bonus', up[2]['type'])
		self.assertEqual('Enclosure/Promo', up[2]['category'])
		self.assertEqual('Efendija', up[0]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=10807', up[0]['contributor']['link'])
		self.assertEqual('2013-10-20T15:40', up[0]['date'])

	def test_media(self):
		html = file(os.path.join(base, 'recent_media.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-20T15:11', data['meta']['edited_date'])
		self.assertEqual('media', data['section'])

		self.assertEqual('new', up[0]['edit'])
		self.assertEqual('N/A', up[0]['catalog'])
		self.assertEqual('album/42368', up[0]['link'])
		self.assertTrue(up[5]['deleted'])
		self.assertEqual('SDEX-0057', up[3]['catalog'])
		self.assertEqual('album/14302', up[3]['link'])
		self.assertEqual('CD', up[3]['media_format'])
		self.assertEqual('Digital', up[-3]['media_format'])

		self.assertEqual('ritsukai', up[0]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=606', up[0]['contributor']['link'])
		self.assertEqual('2013-10-20T15:11', up[0]['date'])

	def test_tracklists(self):
		html = file(os.path.join(base, 'recent_tracklists.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-20T15:17', data['meta']['edited_date'])
		self.assertEqual('tracklists', data['section'])

		self.assertEqual('new', up[0]['edit'])
		self.assertEqual('N/A', up[0]['catalog'])
		self.assertEqual('album/42368', up[0]['link'])
		self.assertEqual('KDSD-00402', up[2]['catalog'])
		self.assertEqual('album/21317', up[2]['link'])
		self.assertEqual('bonus', up[0]['type'])
		self.assertEqual('Enclosure/Promo', up[0]['category'])
		self.assertEqual('game', up[2]['type'])
		self.assertEqual('Game', up[2]['category'])

		self.assertEqual('ritsukai', up[0]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=606', up[0]['contributor']['link'])
		self.assertEqual('2013-10-20T15:17', up[0]['date'])

	def test_scans(self):
		html = file(os.path.join(base, 'recent_scans.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-20T15:43', data['meta']['edited_date'])
		self.assertEqual('scans', data['section'])

		self.assertEqual('deleted', up[0]['edit'])
		self.assertEqual('AICL-2608', up[0]['catalog'])
		self.assertEqual('album/41585', up[0]['link'])
		self.assertEqual('added', up[-1]['edit'])
		self.assertEqual('VICL-60930', up[-1]['catalog'])
		self.assertEqual('album/42362', up[-1]['link'])

		self.assertEqual('Myrkul', up[0]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=65', up[0]['contributor']['link'])
		self.assertEqual('2013-10-20T15:43', up[0]['date'])
		self.assertEqual('boogiepop', up[-1]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=11507', up[-1]['contributor']['link'])
		self.assertEqual('2013-10-20T07:56', up[-1]['date'])

	def test_artists(self):
		html = file(os.path.join(base, 'recent_artists.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-20T14:57', data['meta']['edited_date'])
		self.assertEqual('artists', data['section'])

		self.assertEqual('YSCD-0023', up[0]['linked']['catalog'])
		self.assertEqual('album/29823', up[0]['linked']['link'])
		self.assertTrue(up[0]['deleted'])
		self.assertEqual('Stephen Erdody', up[-1]['names']['en'])
		self.assertEqual('artist/13131', up[-1]['link'])
		self.assertFalse('deleted' in up[-1])

		self.assertEqual('Efendija', up[-1]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=10807', up[-1]['contributor']['link'])
		self.assertEqual('2013-10-20T11:28', up[-1]['date'])

	def test_products(self):
		html = file(os.path.join(base, 'recent_products.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-19T06:50', data['meta']['edited_date'])
		self.assertEqual('products', data['section'])

		self.assertEqual('Album Linkup', up[0]['edit'])
		self.assertEqual('product/1143', up[0]['link'])
		self.assertEqual('Guild Wars 2', up[0]['titles']['en'])
		self.assertEqual('album/42352', up[0]['linked']['link'])
		self.assertEqual('N/A', up[0]['linked']['catalog'])

		self.assertEqual('Lashiec', up[0]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=13861', up[0]['contributor']['link'])
		self.assertEqual('2013-10-19T06:50', up[0]['date'])

	def test_labels(self):
		html = file(os.path.join(base, 'recent_labels.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-20T10:57', data['meta']['edited_date'])
		self.assertEqual('labels', data['section'])

		self.assertEqual('Album Linkup', up[0]['edit'])
		self.assertEqual('org/1022', up[0]['link'])
		self.assertEqual('Varèse Sarabande', up[0]['titles']['en'])
		self.assertEqual('album/42366', up[0]['linked']['link'])
		self.assertEqual('302 066 978 2', up[0]['linked']['catalog'])

		self.assertEqual('Efendija', up[0]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=10807', up[0]['contributor']['link'])
		self.assertEqual('2013-10-20T10:57', up[0]['date'])

		self.assertEqual('Label Page Edit', up[-3]['edit'])
		self.assertEqual('org/1227', up[-3]['link'])
		self.assertEqual('Klang-Gear', up[-3]['titles']['en'])
		self.assertTrue(up[-3]['new'])
		self.assertFalse('linked' in up[-3])

		self.assertEqual('Artist Linkup', up[-4]['edit'])
		self.assertEqual('org/1227', up[-4]['link'])
		self.assertEqual('Klang-Gear', up[-4]['titles']['en'])
		self.assertFalse('new' in up[-4])
		self.assertEqual('artist/14980', up[-4]['linked']['link'])
		self.assertEqual('Martin', up[-4]['linked']['names']['en'])

	def test_links(self):
		html = file(os.path.join(base, 'recent_links.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-20T15:28', data['meta']['edited_date'])
		self.assertEqual('links', data['section'])

		self.assertEqual('Album Link', up[0]['link_type'])
		self.assertEqual('album/42367', up[0]['link'])
		self.assertEqual('N/A', up[0]['catalog'])
		self.assertEqual('Crossfade Demo', up[0]['link_data']['title'])
		self.assertEqual('https://vgmdb.net/redirect/65785/www.amazon.co.jp/dp/B00FXMYERU/', up[1]['link_data']['link'])
		self.assertEqual('amazon.co.jp', up[1]['link_data']['title'])
		self.assertEqual('http://', up[3]['link_data']['link'])
		self.assertEqual('', up[3]['link_data']['title'])

		self.assertEqual('ritsukai', up[0]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=606', up[0]['contributor']['link'])
		self.assertEqual('2013-10-20T15:28', up[0]['date'])

		self.assertEqual('Purchase Link', up[1]['link_type'])
		self.assertEqual('album/41181', up[1]['link'])
		self.assertEqual('REC-092', up[1]['catalog'])

		self.assertEqual('Artist Link', up[6]['link_type'])
		self.assertEqual('artist/2277', up[6]['link'])
		self.assertEqual('Tainokobone', up[6]['names']['en'])

		self.assertEqual('Product Link', up[-1]['link_type'])
		self.assertEqual('product/3282', up[-1]['link'])
		self.assertEqual('Assassination Classroom', up[-1]['names']['en'])

	def test_ratings(self):
		html = file(os.path.join(base, 'recent_ratings.html'), 'r').read()
		data = recent.parse_page(html)
		up = data['updates']

		self.assertTrue('meta' in data)
		self.assertTrue('edited_date' in data['meta'])
		self.assertEqual('2013-10-20T13:34', data['meta']['edited_date'])
		self.assertEqual('ratings', data['section'])

		self.assertEqual('WM-0701~2', up[0]['catalog'])
		self.assertEqual('2013-04-24', up[0]['release_date'])
		self.assertEqual('album/38376', up[0]['link'])
		self.assertEqual('game', up[0]['type'])
		self.assertEqual('Game', up[0]['category'])
		self.assertEqual('Mahou Daisakusen Original Soundtrack', up[0]['titles']['en'])
		self.assertEqual('魔法大作戦 オリジナルサウンドトラック', up[0]['titles']['ja'])
		self.assertEqual('5', up[0]['rating'])

		self.assertEqual('Jodo Kast', up[0]['contributor']['name'])
		self.assertEqual('https://vgmdb.net/forums/member.php?u=1254', up[0]['contributor']['link'])
		self.assertEqual('2013-10-20T13:34', up[0]['date'])


if __name__ == '__main__':
	unittest.main()
