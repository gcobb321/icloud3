

from   homeassistant.util.location import distance

from ..global_variables import GlobalVariables as Gb
from .common            import (round_to_zero, )
from .messaging         import (_trace, _traceha, )


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Distance conversion and formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def km_to_mi(dist_km):
    return float(dist_km) * Gb.um_km_mi_factor

def mi_to_km(dist_mi):
    return round(float(dist_mi) / Gb.um_km_mi_factor, 2)

def km_to_mi_str(dist_km):
    return f"{km_to_mi(dist_km)} {Gb.um}"

#--------------------------------------------------------------------
def m_to_ft(dist_m):
   return float(dist_m) * Gb.um_m_ft_factor

def m_to_ft_str(dist_m):
    return f"{m_to_ft(dist_m)} {Gb.um_m_ft}"

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

    if Gb.um_MI:
        mi = dist_km * Gb.um_km_mi_factor

        if mi >= 100:
            return f"{mi:.0f} mi"
        if mi >= 10:
            return f"{mi:.1f} mi"
        if mi >= 1:
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
    if dist_km >= 100:
        return f"{dist_km:.0f}km"
    if dist_km >= 10:
        return f"{dist_km:.1f}km"
    if dist_km >= 1:
        return f"{dist_km:.2f}km"

    return f"{dist_km*1000:.0f}m"

#--------------------------------------------------------------------
def format_dist_m(dist_m):
    '''
    Reformat the distance based on it's value

    dist: Distance in meters
    '''
    if dist_m >= 1000000:     #100km
        return f"{dist_m/1000:.0f}km"
    if dist_m >= 10000:       #10km
        return f"{dist_m/1000:.1f}km"
    if dist_m >= 1000:        #1km/1000m/.6mi
        return f"{dist_m/1000:.2f}km"

    return f"{dist_m:.0f}m"
