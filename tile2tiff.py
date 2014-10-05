import math
import struct
from collections import Counter

import rasterio

import numpy as np

import scipy
from scipy.stats import norm
import scipy.ndimage


import srtm

import sys

print "Reading file..."

dtype = np.dtype([
    ('lon', np.dtype('<f8')),
    ('lat', np.dtype('<f8')),
    ('ele', np.dtype('<f8'))]
    )

arr = np.fromfile(sys.argv[1], dtype)

# delete some elements from file, known to be stray
arr = arr[(arr['ele']!=1) & (arr['ele']!=100)]

# deduplicate measurements
arr = np.unique(arr)

# count most popular elevation values - sometimes they are stray
countele = Counter(arr['ele'])
print "Most popular elevations:", countele.most_common(10)

# calculating bounding box
minlon = np.amin(arr['lon'])
maxlon = np.amax(arr['lon'])
minlat = np.amin(arr['lat'])
maxlat = np.amax(arr['lat'])
minele = np.amin(arr['ele'])
maxele = np.amax(arr['ele'])
midele = np.mean(arr['ele'])
print "values bbox:", minlon, minlat, maxlon, maxlat
print "elevation range:", minele, maxele, "average elevation:", midele

# removing abnormal values
loc, scale = norm.fit(arr['ele'])
minsaneele, maxsaneele = scipy.stats.norm.interval(0.8, loc=loc, scale=scale)
print "leaving only values between:", minsaneele, maxsaneele
arr = arr[(arr['ele'] > minsaneele) & (arr['ele'] < maxsaneele)]

# calculating size. for simplicity, it's linear 4326 raster, but to have valid
# distance measurements it's scaled by cos(lat) in latitude
midlat = (maxlat + minlat) / 2

xsize = 2048
ysize = int(xsize / 2 / math.cos(math.radians(midlat)))

# getting SRTM data as reference
elevation_data = srtm.get_data()

srtm_raster = np.zeros((xsize, ysize), rasterio.float32)
srtm_count = np.zeros((xsize, ysize), rasterio.float32)

for lat in np.linspace(minlat, maxlat, 500):
    for lon in np.linspace(minlon, maxlon, 500):
        y = (ysize - 1) * (lon - minlon) / (minlon - maxlon)
        x = (xsize - 1) * (lat - minlat) / (maxlat - minlat)
        srtm_raster[x, y] += 6 * elevation_data.get_elevation(lat, lon)#, approximate=True)
        srtm_count[x, y] += 6

# filling voids in SRTM
srtm_count = scipy.ndimage.gaussian_filter(srtm_count, sigma=3.5)
srtm_raster = scipy.ndimage.gaussian_filter(srtm_raster, sigma=3.5)

# creating a copy to snap our data onto
out_raster = srtm_raster[:]
out_count = srtm_count[:]

for rec in arr:
    y = (ysize - 1) * (rec['lon'] - minlon) / (minlon - maxlon)
    x = (xsize - 1) * (rec['lat'] - minlat) / (maxlat - minlat)
    out_raster[x, y] += rec['ele']
    out_count[x, y] += 1

print "Max cell count:", np.amax(out_count)

out_raster[out_count > 100] = 0
out_count[out_count > 100] = 0

out_count = scipy.ndimage.gaussian_filter(out_count, sigma=1.5)
out_raster = scipy.ndimage.gaussian_filter(out_raster, sigma=1.5)

out_count[out_count == 0] = 32767

out_raster /= out_count

diff_raster = out_raster - srtm_raster

print np.mean(diff_raster[out_count != 32767])

with rasterio.drivers():
    with rasterio.open('out_count.tif', mode='w', driver='GTiff', width=xsize, height=ysize, count=1, crs={'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84', 'no_defs': True}, dtype=rasterio.float32, nodata=32767, compress='lzw') as outfile:
        outfile.write_band(1, out_count)
        wld = open('out_count.tfw', 'w')
        print >> wld, -(maxlon - minlon) / xsize
        print >> wld, 0
        print >> wld, 0
        print >> wld, (maxlat - minlat) / ysize
        print >> wld, maxlon
        print >> wld, minlat

with rasterio.drivers():
    with rasterio.open('out.tif', mode='w', driver='GTiff', width=xsize, height=ysize, count=1, crs={'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84', 'no_defs': True}, dtype=rasterio.float32, nodata=0, compress='lzw') as outfile:
        outfile.write_band(1, out_raster)
        wld = open('out.tfw', 'w')
        print >> wld, -(maxlon - minlon) / xsize
        print >> wld, 0
        print >> wld, 0
        print >> wld, (maxlat - minlat) / ysize
        print >> wld, maxlon
        print >> wld, minlat

with rasterio.drivers():
    with rasterio.open('out_diff.tif', mode='w', driver='GTiff', width=xsize, height=ysize, count=1, crs={'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84', 'no_defs': True}, dtype=rasterio.float32, nodata=32767, compress='lzw') as outfile:
        outfile.write_band(1, out_raster)
        wld = open('out_diff.tfw', 'w')
        print >> wld, -(maxlon - minlon) / xsize
        print >> wld, 0
        print >> wld, 0
        print >> wld, (maxlat - minlat) / ysize
        print >> wld, maxlon
        print >> wld, minlat
            #print x, y, rec['ele']



