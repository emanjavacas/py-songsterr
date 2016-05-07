# coding: utf-8

import pycsp.parallel as csp
from songsterr import SongSterr
import requests
from pymongo import MongoClient
import os


def splitjoin(s, sep="_"):
    return sep.join(s.split(" "))


def get_extension(s):
    return s.split(".")[-1]


def fname(song):
    ext = get_extension(song['tab']['guitarProTab']['attachmentUrl'])
    return str(song['song']['id']) + "." + ext


@csp.process
def seeds(songs, start, stop):
    s = SongSterr(summarize=False)
    for i in range(start, stop):
        try:
            song = s.get_tab_by_id(str(i))
            songs(song)
            print "put song {:s}".format(song['song']['title'])
        except requests.HTTPError:
            print "Couldn't find id {:d}".format(i)
        except ValueError:
            print "Missing revision id for {:d}".format(i)
    songs.poison()


@csp.process
def downloads(songs_chan, db_chan, root):
    while True:
        try:
            song = songs_chan()
            with open(os.path.join(root, fname(song)), 'wb') as f:
                url = song['tab']['guitarProTab']['attachmentUrl']
                payload = requests.get(url)
                f.write(payload.content)
            db_chan(song)
        except Exception as e:
            print "Exception when consuming song" + str(e)
    db_chan.poison()
        

@csp.process
def db(db_chan, client):
    while True:
        song = db_chan()
        song['fname'] = fname(song)
        client.insert(song)
    return

    
if __name__ == '__main__':
    db_conn = MongoClient('localhost', 27017)['gp4']
    gp4_client = db_conn.songs
    songs_chan = csp.Channel('songs', buffer=200)
    db_chan = csp.Channel('db')
    par = csp.Parallel(
        [seeds(songs_chan.writer(), i * 1000, 1000 * (i + 1)) for i in range(50, 150)],
        [downloads(songs_chan.reader(), db_chan.writer(), 'data')] * 100,
        [db(db_chan.reader(), gp4_client)] * 10
    )
    csp.shutdown()
