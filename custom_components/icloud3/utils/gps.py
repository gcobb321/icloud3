
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           GPS -- DECIMAL TO DEGREES-MINUTES-SECONDS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def dd_to_dms(lat, lon):
    '''
    Convert (lat, lon) from degrees to degree-minute-second
    '''

    lon_ew  = "E" if lon >= 0 else "W"
    lon_dms = dd_to_dms(lon)
    lat_ns   = "N" if lat >= 0 else "S"
    lat_dms  = dd_to_dms(lat)

    return f"{lat_dms} {lat_ns}, {lon_dms} {lon_ew}"

def decimal_to_dms(decimal):
    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = (decimal - degrees - minutes / 60) * 3600
    return f"{degrees}°{minutes}'{seconds:.2f}\""


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#       CONVERT STANDARD GPS WGS-84 COORDINATES TO CHINESE GCJ-02 AND BD-09
#
#       Based on XYCONVERT.PY, Can Yang, Nov 16, 2020
#           https://github.com/cyang-kth/xyconvert
#
#       Online converter for various formats:
#           https://www.ufreetools.com/en/tool/coordinate-converter
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

import math

a = 6378245.0  # long axis
ee = 0.006693421883570923

def __transform_lat(lat, lon):
    ret = -100.0 + 2.0 * lon + 3.0 * lat + 0.2 * lat * lat + 0.1 * lon * lat + 0.2 * math.sqrt(abs(lon))
    ret = ret + (20.0 * math.sin(6.0 * lon * math.pi) + 20.0 * math.sin(2.0 * lon * math.pi)) * 2.0 / 3.0
    ret = ret + (20.0 * math.sin(lat * math.pi) + 40.0 * math.sin(lat / 3.0 * math.pi)) * 2.0 / 3.0
    ret = ret + (160.0 * math.sin(lat / 12.0 * math.pi) + 320.0 * math.sin(lat * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def __transform_lon(lat, lon):
    ret = 300.0 + lon + 2.0 * lat + 0.1 * lon * lon +  0.1 * lon * lat + 0.1 * math.sqrt(abs(lon))
    ret = ret + (20.0 * math.sin(6.0 * lon * math.pi) + 20.0 * math.sin(2.0 * lon * math.pi)) * 2.0 / 3.0
    ret = ret + (20.0 * math.sin(lon * math.pi) + 40.0 * math.sin(lon / 3.0 * math.pi)) * 2.0 / 3.0
    ret = ret + (150.0 * math.sin(lon / 12.0 * math.pi) + 300.0 * math.sin(lon * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def gcj_to_wgs(gcj_lat, gcj_lon):
    '''
    Convert coordinates GCJ02 to WGS84
    '''
    dlat = __transform_lat(gcj_lat - 35.0, gcj_lon - 105.0)
    dlon = __transform_lon(gcj_lat - 35.0, gcj_lon - 105.0)
    radlat = gcj_lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
    dlon = (dlon * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
    wgs_lat = gcj_lat - dlat
    wgs_lon = gcj_lon - dlon
    return wgs_lat, wgs_lon

def wgs_to_gcj(wgs_lat, wgs_lon):
    '''
    Convert coordinates WGS84 toGCJ02
    '''
    dlat = __transform_lat(wgs_lat - 35.0, wgs_lon - 105.0)
    dlon = __transform_lon(wgs_lat - 35.0, wgs_lon - 105.0)
    radlat = wgs_lat/180.0 * math.pi
    magic =  math.sin(radlat)
    magic  = 1 - ee*magic*magic
    sqrtMagic = math.sqrt(magic)
    dlat = (dlat * 180.0)/((a * (1-ee)) / (magic*sqrtMagic) * math.pi)
    dlon = (dlon * 180.0)/(a/sqrtMagic * math.cos(radlat) * math.pi)
    gcj_lat = wgs_lat + dlat
    gcj_lon = wgs_lon + dlon
    return gcj_lat, gcj_lon

def bd_to_gcj(bd_lat, bd_lon):
    '''
    Convert coordinates BD09 to GCJ02
    '''
    y = bd_lat - 0.006
    x = bd_lon - 0.0065
    z = math.sqrt(pow(x,2) + pow(y,2)) - 0.00002 * math.sin(y * math.pi * 3000.0/180.0)
    theta = math.atan2(y,x) - 0.000003 * math.cos(x * math.pi *3000.0/180.0)
    gcj_lat = z * math.sin(theta)
    gcj_lon = z * math.cos(theta)
    return gcj_lat, gcj_lon

def gcj_to_bd(gcj_lat, gcj_lon):
    '''
    Convert coordinates GCJ02 to BD09
    '''
    z = math.sqrt(pow(gcj_lat,2) + pow(gcj_lon,2)) + 0.00002 * math.sin(gcj_lat * math.pi * 3000.0/180.0)
    theta = math.atan2(gcj_lat, gcj_lon) + 0.000003 * math.cos(gcj_lon * math.pi * 3000.0/180.0)
    bd_lat = z * math.sin(theta) + 0.006
    bd_lon = z * math.cos(theta) + 0.0065
    return bd_lat, bd_lon

def bd_to_wgs(bd_lat, bd_lon):
    '''
    Convert coordinates BD09 to WGS84
    '''
    gcj_lat, gcj_lon = bd_to_gcj(bd_lat, bd_lon)
    return gcj_to_wgs(gcj_lat, gcj_lon)

def wgs_to_bd(wgs_lat, wgs_lon):
    '''
    Convert coordinates WGS84 to BD09
    '''
    gcj_lat, gcj_lon = wgs_to_gcj(wgs_lat, wgs_lon)
    return gcj_to_bd(gcj_lat, gcj_lon)
