# -*- coding: UTF-8 -*-
import os
import unittest

from vgmdb.parsers import album

base = os.path.dirname(__file__)

class TestAlbums(unittest.TestCase):
	def setUp(self):
		pass

	def test_ff8(self):
		ff8_code = file(os.path.join(base, 'album_ff8.html'), 'r').read()
		ff8 = album.parse_page(ff8_code)

		self.assertEqual("FITHOS LUSEC WECOS VINOSEC: FINAL FANTASY VIII [Limited Edition]", ff8['names']['en'])
		self.assertEqual("FITHOS LUSEC WECOS VINOSEC: FINAL FANTASY VIII [Limited Edition]", ff8['names']['ja'])
		self.assertEqual("SSCX-10037", ff8['catalog'])
		self.assertEqual("MICA-0277", ff8['reprints'][2]['catalog'])
		self.assertEqual(5, len(ff8['reprints']))
		self.assertEqual("1999-11-20", ff8['release_date'])
		self.assertEqual("Commercial, Limited Edition", ff8['publish_format'])
		self.assertEqual(2854.0, ff8['release_price']['price'])
		self.assertEqual("JPY", ff8['release_price']['currency'])
		self.assertEqual("CD", ff8['media_format'])
		self.assertEqual("Arrangement", ff8['classification'])
		self.assertEqual("DigiCube", ff8['publisher']['names']['en'])
		self.assertEqual("株式会社デジキューブ", ff8['publisher']['names']['ja'])
		self.assertEqual("org/54", ff8['publisher']['link'])
		self.assertEqual("DigiCube", ff8['organizations'][0]['names']['en'])
		self.assertEqual("株式会社デジキューブ", ff8['organizations'][0]['names']['ja'])
		self.assertEqual("org/54", ff8['organizations'][0]['link'])
		self.assertEqual("publisher", ff8['organizations'][0]['role'])
		self.assertEqual("SME Intermedia Inc.", ff8['distributor']['names']['en'])
		self.assertEqual("org/186", ff8['distributor']['link'])
		self.assertEqual("SME Intermedia Inc.", ff8['organizations'][1]['names']['en'])
		self.assertEqual("org/186", ff8['organizations'][1]['link'])
		self.assertEqual("distributor", ff8['organizations'][1]['role'])
		self.assertEqual("Nobuo Uematsu", ff8['composers'][0]['names']['en'])
		self.assertEqual("Shiro Hamaguchi", ff8['arrangers'][0]['names']['en'])
		self.assertEqual("artist/125", ff8['arrangers'][0]['link'])
		self.assertEqual("Faye Wong", ff8['performers'][0]['names']['en'])
		self.assertEqual("Kazushige Nojima", ff8['lyricists'][0]['names']['en'])
		self.assertEqual(1, len(ff8['discs']))
		self.assertEqual(13, len(ff8['discs'][0]['tracks']))
		self.assertEqual("3:09", ff8['discs'][0]['tracks'][0]['track_length'])
		self.assertEqual("Liberi Fatali", ff8['discs'][0]['tracks'][0]['names']['English'])
		self.assertEqual("64:16", ff8['discs'][0]['disc_length'])
		self.assertEqual(4.44, ff8['rating'])
		self.assertEqual(57, ff8['votes'])
		self.assertEqual("Game", ff8['category'])
		self.assertEqual("Final Fantasy VIII", ff8['products'][0]['names']['en'])
		self.assertEqual("ファイナルファンタジーVIII", ff8['products'][0]['names']['ja'])
		self.assertEqual("product/189", ff8['products'][0]['link'])
		self.assertEqual("Sony PlayStation", ff8['platforms'][0])
		self.assertEqual("RPGFan's Review", ff8['websites']['Review'][0]['name'])
		self.assertEqual("Booklet Front", ff8['covers'][0]['name'])
		self.assertEqual("https://medium-media.vgm.io/albums/97/79/79-1264618929.png", ff8['picture_small'])
		self.assertEqual("https://media.vgm.io/albums/97/79/79-1264618929.png", ff8['picture_full'])
		self.assertEqual("https://thumb-media.vgm.io/albums/97/79/79-1264618929.png", ff8['covers'][0]['thumb'])
		self.assertEqual("https://medium-media.vgm.io/albums/97/79/79-1264618929.png", ff8['covers'][0]['medium'])
		self.assertEqual("https://media.vgm.io/albums/97/79/79-1264618929.png", ff8['covers'][0]['full'])
		self.assertEqual("EYES ON ME: featured in FINAL FANTASY VIII", ff8['related'][0]['names']['en'])
		self.assertEqual("PRT-8429", ff8['related'][0]['catalog'])
		self.assertEqual("bonus", ff8['related'][0]['type'])
		self.assertEqual("2006-08-03T01:33", ff8['meta']['added_date'])
		self.assertEqual("2020-08-07T19:45", ff8['meta']['edited_date'])
		self.assertEqual(18238, ff8['meta']['visitors'])
		self.assertEqual(35, ff8['meta']['freedb'])

	def test_arciel(self):
		arciel_code = file(os.path.join(base, 'album_arciel.html'), 'r').read()
		arciel = album.parse_page(arciel_code)

		self.assertEqual("Ar tonelico III Image CD Utau Oka ~Ar=Ciel Ar=Dor~", arciel['names']['en'])
		self.assertEqual("アルトネリコ3 イメージCD 謳う丘～Ar=Ciel Ar=Dor～", arciel['names']['ja'])
		self.assertEqual("FCCM-0328", arciel['catalog'])
		self.assertEqual("謳う丘 ～Ar=Ciel Ar=Dor～", arciel['discs'][0]['tracks'][0]['names']['Japanese'])
		self.assertEqual("CDJapan", arciel['stores'][0]['name'])
		self.assertTrue("Akiko Shikata" in arciel['notes'])

	def test_at3(self):
		at3_code = file(os.path.join(base, 'album_at3.html'), 'r').read()
		at3 = album.parse_page(at3_code)
		self.assertEqual(2, len(at3['discs']))
		self.assertEqual('EXEC_FLIP_FUSIONSPHERE/.', at3['discs'][1]['tracks'][3]['names']['Romaji'])
	def test_viking(self):
		viking_code = file(os.path.join(base, 'album_viking.html'), 'r').read()
		viking = album.parse_page(viking_code)

		self.assertEqual('Free', viking['release_price']['price'])
		self.assertEqual(2099, viking['meta']['visitors'])
		self.assertEqual('NES (Famicom)', viking['platforms'][0])
		self.assertEqual('Duty Cycle Generator', viking['publisher']['names']['en'])

	def test_blooming(self):
		blooming_code = file(os.path.join(base, 'album_blooming.html'), 'r').read()
		blooming = album.parse_page(blooming_code)

		self.assertEqual('KMCM-2', blooming['catalog'])
		self.assertEqual('KMDA-5', blooming['related'][0]['catalog'])
		self.assertEqual('2000-08-03', blooming['related'][0]['date'])
		self.assertEqual('KMCA-65', blooming['related'][1]['catalog'])
		self.assertEqual('2000-09-21', blooming['related'][1]['date'])
		self.assertEqual('CDJapan (OOP)', blooming['stores'][0]['name'])

	def test_istoria(self):
		istoria_code = file(os.path.join(base, 'album_istoria.html'), 'r').read()
		istoria = album.parse_page(istoria_code)

		self.assertEqual('Tomoki Yamada', istoria['performers'][-1]['names']['en'])
		self.assertEqual('Vocal, Original Work', istoria['classification'])
		self.assertEqual('Comic Market 81', istoria['release_events'][0]['name'])
		self.assertEqual('C81', istoria['release_events'][0]['shortname'])
		self.assertEqual('event/146', istoria['release_events'][0]['link'])

	def test_zwei(self):
		zwei_code = file(os.path.join(base, 'album_zwei.html'), 'r').read()
		zwei = album.parse_page(zwei_code)
		self.assertEqual(5, len(zwei['composers']))
		self.assertEqual('Falcom Sound Team jdk', zwei['composers'][0]['names']['en'])
		self.assertEqual('artist/293', zwei['composers'][0]['link'])
		self.assertEqual('Atsushi Shirakawa', zwei['composers'][1]['names']['en'])

	def test_bootleg(self):
		bootleg_code = file(os.path.join(base, 'album_bootleg.html'), 'r').read()
		bootleg = album.parse_page(bootleg_code)
		self.assertEqual('GAME-119', bootleg['catalog'])
		self.assertEqual(True, bootleg['bootleg'])
		self.assertEqual('album/722', bootleg['bootleg_of']['link'])
		self.assertEqual('N30D-021', bootleg['bootleg_of']['catalog'])

	def test_brokennight(self):
		# has a linked release
		night_code = file(os.path.join(base, 'album_brokennight.html'), 'r').read()
		night = album.parse_page(night_code)
		self.assertEqual('DFCL-2101~2', night['catalog'])
		self.assertEqual('Sony PlayStation Vita', night['platforms'][0])
		self.assertEqual('release/3993', night['products'][0]['link'])
		self.assertEqual('Unknown', night['discs'][1]['tracks'][0]['track_length'])
		self.assertEqual('Unknown', night['discs'][1]['disc_length'])

	def test_touhou(self):
		# has multiple releases
		touhou_code = file(os.path.join(base, 'album_touhou.html'), 'r').read()
		touhou = album.parse_page(touhou_code)
		self.assertEqual('IO-0212', touhou['catalog'])
		self.assertEqual(2, len(touhou['release_events']))
		self.assertEqual('event/155', touhou['release_events'][0]['link'])
		self.assertEqual('Touhou Kouroumu 8', touhou['release_events'][0]['shortname'])
		self.assertEqual('Touhou Kouroumu 8', touhou['release_events'][0]['name'])
		self.assertEqual('event/152', touhou['release_events'][1]['link'])
		self.assertEqual('M3-30', touhou['release_events'][1]['shortname'])
		self.assertEqual('M3-2012 Fall', touhou['release_events'][1]['name'])

	def test_million(self):
		# has multiple publishers
		million_code = file(os.path.join(base, 'album_million.html'), 'r').read()
		million = album.parse_page(million_code)
		self.assertEqual(3, len(million['organizations']))
		self.assertEqual('Key Sounds Label', million['publisher']['names']['en'])
		self.assertEqual('Key Sounds Label', million['publisher']['names']['ja'])
		self.assertEqual('org/1', million['publisher']['link'])
		self.assertEqual('Key Sounds Label', million['organizations'][0]['names']['en'])
		self.assertEqual('Key Sounds Label', million['organizations'][0]['names']['ja'])
		self.assertEqual('org/1', million['organizations'][0]['link'])
		self.assertEqual('label', million['organizations'][0]['role'])
		self.assertEqual("VISUAL ARTS Co., Ltd.", million['organizations'][1]['names']['en'])
		self.assertEqual('株式会社ビジュアルアーツ', million['organizations'][1]['names']['ja'])
		self.assertEqual('org/429', million['organizations'][1]['link'])
		self.assertEqual('manufacturer', million['organizations'][1]['role'])
		self.assertEqual("VISUAL ARTS Co., Ltd.", million['organizations'][2]['names']['en'])
		self.assertEqual('株式会社ビジュアルアーツ', million['organizations'][2]['names']['ja'])
		self.assertEqual('org/429', million['organizations'][2]['link'])
		self.assertEqual('distributor', million['organizations'][2]['role'])

	def test_got(self):
		# used to have unlinked publisher and a distributor
		got_code = file(os.path.join(base, 'album_got.html'), 'r').read()
		got = album.parse_page(got_code)
		self.assertEqual(2, len(got['organizations']))
		self.assertEqual('Game Audio Factory', got['publisher']['names']['en'])
		self.assertEqual('org/1636', got['publisher']['link'])
		self.assertEqual('Bandcamp', got['distributor']['names']['en'])
		self.assertEqual('org/965', got['distributor']['link'])
if __name__ == '__main__':
	unittest.main()
