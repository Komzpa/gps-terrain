#!/usr/bin/env python2
import os
import sys
import struct

def deg2num(lat_deg, lon_deg, zoom):
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((lat_deg + 90.0) / 180.0 * n)
    return (xtile, ytile)

def tilename(lat, lon, zoom, extension = ''):
    x, y = deg2num(lat, lon, zoom)
    return "%(zoom)s/%(x)s/%(y)s.%(extension)s" % locals()


def process():
    fname = ""
    fhandle = open('/dev/null', 'a')
    sys.stdin.readline()
    tile_zoom = 13
    lineno = 0
    for line in sys.stdin:
        lineno += 1
        lat, lon, ele = line.strip().split(',')
        ele = float(ele)
        if ele < -1000 or ele == 0 or ele > 9000:
            continue
        lat = int(lat)/1.0e7
        lon = int(lon)/1.0e7
        #print lat, lon, ele
        newfname = tilename(lat, lon, tile_zoom)
        if fname != newfname:
            fhandle.close()
            fname = newfname
            directory = os.path.dirname(fname)
            if not os.path.exists(directory):
                os.makedirs(directory)
            fhandle = open(fname, 'ab')
        fhandle.write(struct.pack('!ddd', lon, lat, ele))
        if lineno % 10000 == 0:
            print lineno

process()