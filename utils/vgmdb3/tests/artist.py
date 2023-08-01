# -*- coding: UTF-8 -*-
import os
import unittest

from vgmdb.parsers import artist

base = os.path.dirname(__file__)

class TestArtists(unittest.TestCase):
	def setUp(self):
		pass

	def test_nobuo(self):
		nobuo_code = file(os.path.join(base, 'artist_nobuo.html'), 'r').read()
		nobuo = artist.parse_page(nobuo_code)
		self.assertEqual('Nobuo Uematsu', nobuo['name'])
		self.assertEqual('male', nobuo['sex'])
		self.assertEqual('Mar 21, 1959', nobuo['info']['Birthdate'])
		self.assertEqual('1959-03-21', nobuo['birthdate'])
		self.assertEqual(1, len(nobuo['info']['Organizations']))
		self.assertEqual(1, len(nobuo['organizations']))
		self.assertEqual('Dog Ear Records', nobuo['info']['Organizations'][0]['names']['en'])
		self.assertEqual('Dog Ear Records', nobuo['organizations'][0]['names']['en'])
		self.assertEqual('Individual', nobuo['type'])
		self.assertEqual('Earthbound Papas', nobuo['units'][0]['names']['en'])
		self.assertEqual('CRUISE CHASER BLASSTY', nobuo['discography'][0]['titles']['en'])
		self.assertEqual('album/11113', nobuo['discography'][0]['link'])
		self.assertEqual('album/718', nobuo['featured_on'][0]['link'])
		self.assertEqual('bonus', nobuo['discography'][0]['type'])
		self.assertEqual('1986-04-26', nobuo['discography'][0]['date'])
		self.assertEqual('H25X-20015', nobuo['discography'][2]['catalog'])
		self.assertTrue('Composer' in nobuo['discography'][0]['roles'])
		self.assertEqual('DOGEARRECORDS', nobuo['websites']['Official'][0]['name'])
		self.assertEqual('UematsuNobuo', nobuo['twitter_names'][0])
		self.assertEqual('2007-10-17T09:14', nobuo['meta']['added_date'])
		self.assertEqual('https://thumb-media.vgm.io/artists/77/77/77-1345913713.jpg', nobuo['picture_small'])
		self.assertEqual('https://media.vgm.io/artists/77/77/77-1345913713.jpg', nobuo['picture_full'])

	def test_nobuo_name(self):
		""" Japanese name """
		nobuo_name = "植松 伸夫 (うえまつ のぶお)"
		name_info = artist._parse_full_name(nobuo_name)
		self.assertEqual('植松 伸夫', name_info['name_real'])
		self.assertEqual('うえまつ のぶお', name_info['name_trans'])

	def test_black_mages_name(self):
		""" no trans name """
		blackmages_name = "ザ・ブラックメイジーズ"
		name_info = artist._parse_full_name(blackmages_name)
		self.assertEqual('ザ・ブラックメイジーズ', name_info['name_real'])
		self.assertTrue('name_trans' not in name_info)

	def test_sungwoon_name(self):
		""" Korean name """
		sung_name = "장 성운 (ジャン ソンウン)"
		name_info = artist._parse_full_name(sung_name)
		self.assertEqual( '장 성운',name_info['name_real'])
		self.assertEqual('ジャン ソンウン', name_info['name_trans'])

	def test_jeremy_name(self):
		""" English names don't have anything in this field """
		jeremy_name = ""
		name_info = artist._parse_full_name(jeremy_name)
		self.assertEqual(0, len(list(name_info.keys())))

	def test_ss(self):
		ss_code = file(os.path.join(base, 'artist_ss.html'), 'r').read()
		ss = artist.parse_page(ss_code)
		self.assertEqual('Composer (as HAPPY-SYNTHESIZER)', ss['discography'][13]['roles'][0])
		self.assertEqual('Arranger (as (S_S))', ss['discography'][14]['roles'][0])
		self.assertEqual('DIRTY-SYNTHESIZER', ss['aliases'][1]['names']['en'])
		self.assertEqual('HAPPY-SYNTHESIZER', ss['aliases'][3]['names']['en'])
		self.assertEqual('Takeshi Nagai', ss['members'][0]['names']['en'])
		self.assertEqual('2011-10-03T05:45', ss['meta']['edited_date'])
		self.assertEqual('Unit', ss['type'])

	def test_s_s(self):
		# sexy synthesizer alias
		ss_code = file(os.path.join(base, 'artist_s_s.html'), 'r').read()
		ss = artist.parse_page(ss_code)
		self.assertEqual('(S_S)', ss['name'])
		self.assertEqual('Alias', ss['type'])

	def test_offenbach(self):
		offenbach_code = file(os.path.join(base, 'artist_offenbach.html'), 'r').read()
		offenbach = artist.parse_page(offenbach_code)
		self.assertEqual('Jacques Offenbach', offenbach['name'])
		self.assertEqual('male', offenbach['sex'])
		self.assertEqual('Individual', offenbach['type'])
		self.assertEqual('1819-06-20', offenbach['birthdate'])
		self.assertEqual('1880-10-05', offenbach['deathdate'])

	def test_key(self):
		key_code = file(os.path.join(base, 'artist_key.html'), 'r').read()
		key = artist.parse_page(key_code)
		self.assertEqual('Jun Maeda', key['name'])
		self.assertEqual('Individual', key['type'])
		self.assertEqual('male', key['sex'])
		self.assertEqual(1, len(key['aliases']))
		self.assertEqual('KEY', key['aliases'][0]['names']['en'])

	def test_rookies(self):
		rookies_code = file(os.path.join(base, 'artist_rookies.html'), 'r').read()
		rookies = artist.parse_page(rookies_code)
		self.assertEqual("ROOKiEZ is PUNK'D", rookies['name'])
		self.assertEqual(3, len(rookies['info']['Members']))
		self.assertEqual('Unit', rookies['type'])
		self.assertFalse('link' in rookies['info']['Members'][0])
		self.assertEqual('RYOTA', rookies['info']['Members'][0]['names']['en'])
		self.assertEqual('artist/15569', rookies['info']['Members'][2]['link'])
		self.assertEqual('SHiNNOSUKE', rookies['info']['Members'][2]['names']['en'])
		self.assertFalse('link' in rookies['info']['Former Members'][0])
		self.assertEqual('2RASH', rookies['info']['Former Members'][0]['names']['en'])

	def test_horie(self):
		horie_code = file(os.path.join(base, 'artist_horie.html'), 'r').read()
		horie = artist.parse_page(horie_code)
		self.assertEqual('B', horie['info']['Bloodtype'])

if __name__ == '__main__':
	unittest.main()
