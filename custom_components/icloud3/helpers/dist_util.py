

from   homeassistant.util.location import distance

from ..global_variables import GlobalVariables as Gb
from .common            import (round_to_zero, )
from .messaging         import (_trace, _traceha, )


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Distance conversion and formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def km_to_mi(distance):
    """
    convert km to miles
    """
    #try:
    return distance * Gb.um_km_mi_factor

    #     mi = distance * Gb.um_km_mi_factor

    #     if mi == 0:
    #         mi = 0
    #     elif mi < 1:
    #         mi = float(f"{mi:.2f}")
    #     elif mi < 20:
    #         mi = float(f"{mi:.1f}")
    #     else:
    #         mi = round(mi)

    # except:
    #     mi = 0

    # return mi

def mi_to_km(distance):
    return round(float(distance) / Gb.um_km_mi_factor, 2)

def km_to_mi_str(distance):
    return f"{km_to_mi(distance)} {Gb.um}"
#--------------------------------------------------------------------
def m_to_ft(distance):
    return km_to_mi(distance)

def m_to_ft_str(distance):
    return f"{m_to_ft(distance)} {Gb.um_m_ft}"
#--------------------------------------------------------------------
def calc_distance_km(from_gps, to_gps):

    distance_m = calc_distance_m(from_gps, to_gps)
    return round_to_zero(distance_m/1000)

#--------------------------------------------------------------------
def calc_distance_m(from_gps, to_gps):
    from_lat, from_long = from_gps
    to_lat, to_long     = to_gps

    if (from_lat is None or from_long is None or to_lat is None or to_long is None
            or from_lat == 0  or from_long == 0 or to_lat == 0 or to_long == 0):
        return 0

    distance_m = distance(from_lat, from_long, to_lat, to_long)
    distance_m = round_to_zero(distance_m)
    distance_m = 0 if distance_m < .002 else distance_m
    return distance_m
    return round_to_zero(distance_m)

    # distance_m = distance(from_lat, from_long, to_lat, to_long)
    # return round_to_zero(distance_m)

#--------------------------------------------------------------------
def format_km_to_mi(dist_km):
    '''
    Reformat the distance based on it's value

    dist: Distance in kilometers
    '''

    if Gb.um == 'mi':
        mi = dist_km * Gb.um_km_mi_factor

        if mi > 10:
            return f"{mi:.1f} mi"
        if mi > 1:
            return f"{mi:.2f} mi"
        if round_to_zero(mi) == 0:
            return f"0 mi"
        return f"{mi:.2f} mi"

    return format_dist_km(dist_km)

#--------------------------------------------------------------------
def format_dist_km(dist_km):
    '''
    Reformat the distance based on it's value

    dist: Distance in kilometers
    '''
    if dist_km >= 10:       #25km/15mi
        return f"{dist_km:.1f}km"
    if dist_km >= 1:        #1000m/.6mi
        return f"{dist_km:.2f}km"

    return f"{dist_km*1000:.0f}m"

#--------------------------------------------------------------------
def format_dist_m(dist_m):
    '''
    Reformat the distance based on it's value

    dist: Distance in meters
    '''
    if dist_m >= 10000:       #25km/15mi
        return f"{dist_m/1000:.1f}km"
    if dist_m >= 1000:        #1000m/.6mi
        return f"{dist_m/1000:.2f}km"

    return f"{dist_m:.0f}m"
