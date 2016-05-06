import pycsp.parallel as csp
from songsterr import SongSterr
import requests
import os


def splitjoin(s, sep="_"):
    return sep.join(s.split(" "))


def get_extension(s):
    return s.split(".")[-1]


@csp.process
def seeds(songs, start, stop):
    s = SongSterr()
    for i in range(start, stop):
        try:
            song = s.get_tab_by_id(str(i))
            songs(song)
            print "put song {:s}".format(song['title'])
        except requests.HTTPError:
            print "Couldn't find id {:d}".format(i)
        except ValueError:
            print "Missing revision id for {:d}".format(i)
    return


@csp.process
def downloads(songs, root):
    while True:
        song = songs()
        artist = splitjoin(song['artist']['name'])
        title = splitjoin(song['title'])
        fname = artist + "-" + title + "." + get_extension(song['gp5'])
        with open(os.path.join(root, fname), 'wb') as f:
            payload = requests.get(song['gp5'])
            content = payload.raw.read()
            f.write(content)

if __name__ == '__main__':
    songs = csp.Channel('songs', buffer=200)
    par = csp.Parallel(
        seeds(songs.writer(), 500, 100000),
        downloads(songs.reader(), 'data') * 100
    )
    csp.shutdown()
