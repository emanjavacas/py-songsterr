# coding: utf-8

import requests
import re
from bs4 import BeautifulSoup

VALID_SONG_URL = r'/http:\/\/www.songsterr.com\/a\/wsa\/.+s\d+t\d+/i'
REVISION_ID = r'\d+(?=&demoSong)'


class SongSterr(object):
    def __init__(self, encoding="json"):
        self.encoding = encoding

    def _url(self, path):
        return 'http://www.songsterr.com' + path

    def _revision_url(self, revision_id):
        path = 'http://www.songsterr.com/a/ra/player/songrevision/{id}.{enc}'
        return path.format(id=revision_id, enc=self.encoding)

    def _is_valid_song(self, url):
        return re.match(VALID_SONG_URL, url)

    def get_tab_by_id(self, id):
        resp = requests.get(self._url("/a/wa/song?id={id}".format(id=id)))
        try:
            redirect = resp.url
        except AttributeError:
            raise ValueError("Wrong id?")
        return self.get_tab_by_url(redirect)

    def get_tab_by_url(self, url):
        resp = requests.get(url)
        if resp.status_code == 200:
            revision_id = re.findall(REVISION_ID, resp.text)
            if revision_id:
                return self.get_tab_by_revision_id(revision_id[0])
            else:
                raise ValueError("No revision id found in page")
        else:
            resp.raise_for_status()

    def get_tab_by_revision_id(self, revision_id):
        resp = requests.get(self._revision_url(revision_id))
        if resp.status_code == 200:
            resp_json = resp.json()
            output = {}
            output['artist'] = {}
            output['artist']['id'] = resp_json['song']['artist']['id']
            output['artist']['name'] = resp_json['song']['artist']['name']
            output['title'] = resp_json['song']['title']
            output['gp5'] = resp_json['tab']['guitarProTab']['attachmentUrl']
            output['songId'] = resp_json['song']['id']
            output['tabId'] = resp_json['tab']['id']
            return output
        else:
            resp.raise_for_status()
