if __name__ == '__main__':
    from vgmdb3.vgmdb.parsers.search import fetch_page as fetch_search_page
    from vgmdb3.vgmdb.parsers.album import fetch_page as fetch_album_page
    from vgmdb3.vgmdb.parsers.album import parse_page as parse_album_page
    from configs import *
else:
    from .vgmdb3.vgmdb.parsers.search import fetch_page as fetch_search_page
    from .vgmdb3.vgmdb.parsers.search import parse_page as parse_search_page
    from .vgmdb3.vgmdb.parsers.album import fetch_page as fetch_album_page
    from .vgmdb3.vgmdb.parsers.album import parse_page as parse_album_page
    from configs import *

import re
import time


def searchVGMDB(query:str, retry:int = 3) -> dict:
    tried = 0
    while tried < retry:
        try:
            return parse_search_page(fetch_search_page(query))
        except Exception as e:
            tried += 1
            time.sleep(tried)
    return {}


def getVGMDBAlbumInfo(album_id:int|str, retry:int = 3) -> dict:
    tried = 0
    while tried < retry:
        try:
            return parse_album_page(fetch_album_page(str(album_id)))
        except Exception as e:
            tried += 1
            time.sleep(tried)
    return {}



class AlbumInfoVGMDB:


    def __init__(self, info_dict:dict) -> None:
        self.d = info_dict


    @property
    def names(self) -> list[str]:
        return list(self.d.get('names', {}).values())


    @property
    def artists(self) -> list:
        artists = []
        for performer in self.d['performers']:
            artists += list(performer['names'].values())
        for composer in self.d['composers']:
            artists += list(composer['names'].values())
        for arranger in self.d['arrangers']:
            artists += list(arranger['names'].values())
        return artists


    @property
    def num_discs(self) -> int:
        return len(self.d.get('discs', []))


    @property
    def media_format(self) -> str:
        return self.d.get('media_format', '')


    @property
    def num_cd(self) -> int:
        if 'CD' in self.media_format:
            n_cd = self.media_format.split('CD')[0]
            return int(n_cd.strip()) if n_cd else 1
        else:
            return 0


    @property
    def catalog(self) -> str:
        return self.d.get('catalog', '')


    @property
    def cd_catalogs(self) -> list[str]:
        # TODO: this function cannot handle catalog like 'KICA-100A-B'
        if m := re.match(VGMDB_CATALOG_PATTERN, self.catalog):
            prefix, start, end = m.group('prefix'), m.group('start'), m.group('end')
            prefix = prefix.strip()
            start = int(start)
            return [(prefix + str(idx)) for idx in range(start, start + self.num_cd)]
        return [self.catalog]

    @property
    def catalogs(self) -> list[str]:
        # TODO: this function cannot handle catalog like 'KICA-100A-B'
        if m := re.match(VGMDB_CATALOG_PATTERN, self.catalog):
            prefix, start, end = m.group('prefix'), m.group('start'), m.group('end')
            prefix = prefix.strip()
            start = int(start)
            return [(prefix + str(idx)) for idx in range(start, start + self.num_discs)]
        return [self.catalog]




    @property
    def barcode(self) -> str:
        return self.d.get('barcode', '')


    @property
    def classifications(self) -> list[str]:
        return self.d.get('classification', '').split(', ')


    @property
    def publish_formats(self) -> list[str]:
        return self.d.get('publish_format', '').split(', ')


    @property
    def year(self) -> int:
        if m := re.match(VGMDB_DATE_FORMAT, self.d.get('release_date', '')):
            return int(m.group('year'))
        return 1900


    @property
    def month(self) -> int:
        if m := re.match(VGMDB_DATE_FORMAT, self.d.get('release_date', '')):
            return int(m.group('month'))
        return 0


    @property
    def day(self) -> int:
        if m := re.match(VGMDB_DATE_FORMAT, self.d.get('release_date', '')):
            return int(m.group('day'))
        return 0


    @property
    def release_date(self) -> str:
        return self.d.get('release_date', '')


    @property
    def yymmdd(self) -> str:
        return self.d.get('release_date', '').replace('-', '')[2:]


    @property
    def is_bonus(self) -> bool:
        if 'Enclosure' in self.publish_formats:
            return True
        note = self.d.get('note', '').lower()
        if any(keyword in note for keyword in VGMDB_BONUS_CD_KEYWORDS):
            return True
        return False




if __name__ == '__main__':
    sr = searchVGMDB('kemurikusa')
    ar = getVGMDBAlbumInfo(87600)
    ai = AlbumInfoVGMDB(ar)

    print(ai.cd_catalogs)

    input('DEBUG OK!')
