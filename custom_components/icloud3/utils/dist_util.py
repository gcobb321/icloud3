

from   homeassistant.util.location import distance

from ..const            import (NEAR_DEVICE_DISTANCE, LT, )
from ..global_variables import GlobalVariables as Gb
from .utils             import (round_to_zero, isnumber, )
from .messaging         import (_evlog, _log, )
from .time_util         import (format_secs_since, )

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Distance calculation and conversion functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def gps_distance_km(from_gps, to_gps):

    dist_m = gps_distance_m(from_gps, to_gps)
    return round(dist_m/1000, 8)
    #return round_to_zero(dist_m/1000)

#--------------------------------------------------------------------
def gps_distance_m(from_gps, to_gps):
    from_lat, from_long = from_gps
    to_lat, to_long     = to_gps

    if (from_lat is None or from_long is None or to_lat is None or to_long is None
            or from_lat == 0  or from_long == 0 or to_lat == 0 or to_long == 0):
        return 0.0

    dist_m = distance(from_lat, from_long, to_lat, to_long)

    return round(dist_m, 8)

#--------------------------------------------------------------------
def km_to_mi(dist_km):
    return round(float(dist_km) * Gb.um_km_mi_factor, 8)

#--------------------------------------
def mi_to_km(dist_mi):
    return round(float(dist_mi) / Gb.um_km_mi_factor, 8)

#--------------------------------------
def m_to_ft(dist_m):
   return round(float(dist_m) * Gb.um_m_ft_factor, 8)

#-------------------------------------------------------------------------------------------
def set_precision(dist, um=None):
    '''
    Return the distance value as an integer or float value
    '''
    try:
        if isnumber(dist) is False:
            return dist

        um = um if um else Gb.um
        precision = 5 if um in ['km', 'mi'] else 2 if um in ['m', 'ft'] else 4
        dist = round(float(dist), precision)

    except Exception as err:
        pass

    return dist

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Distance string formatting functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>-
def m_to_um_ft(dist_m, as_integer=False):

    if Gb.um_KM:
        if round_to_zero(dist_m) == 0: return "0.0m"
        if as_integer: return f"{int(dist_m)}m"
        return f"{dist_m:.1f}m"

    dist_ft = m_to_ft(dist_m)
    if round_to_zero(dist_ft) == 0: return "0.0ft"
    if as_integer: return f"{int(dist_ft)}ft"
    return f"{dist_ft:.1f}ft"

#--------------------------------------------------------------------
def m_to_um(dist_m):
    return km_to_um(dist_m / 1000)

def km_to_um(dist_km):
    if Gb.um_KM:
        return format_dist_km(dist_km)

    dist_mi = dist_km * Gb.um_km_mi_factor
    return format_dist_mi(dist_mi)

#--------------------------------------
def format_dist_m(dist_m):

    dist_km = dist_m / 1000
    return format_dist_km(dist_km)

#--------------------------------------
def format_dist_km(dist_km):

    if dist_km < 0:
        dist_km = abs(dist_km)

    if dist_km >= 100: return f"{dist_km:.0f}km".replace('.0', '')
    if dist_km >= 10:  return f"{dist_km:.1f}km"
    if dist_km >= 1:   return f"{dist_km:.2f}km"
    dist_m = dist_km * 1000
    if dist_m >= 1:    return f"{dist_m:.0f}m"
    if round_to_zero(dist_km) == 0: return f"0.0km"
    return f"{dist_m:.1f}m"

#--------------------------------------------------------------------
def format_dist_mi(dist_mi):

    if dist_mi < 0:
        dist_mi = abs(dist_mi)

    if dist_mi >= 100:     return f"{dist_mi:.0f}mi".replace('.0', '')
    if dist_mi >= 10:      return f"{dist_mi:.1f}mi"
    if dist_mi >= 1:       return f"{dist_mi:.1f}mi"
    if dist_mi >= .0947:   return f"{dist_mi:.2f}mi"
    dist_ft = dist_mi * 5280
    if dist_ft >= 1:       return f"{dist_ft:.1f}ft"
    if round_to_zero(dist_mi) == 0: return f"0.0mi"
    return f"{dist_ft:.2f}ft"

#--------------------------------------------------------------------
def reformat_um(dist):
    if type(dist) is not str:
        return dist

    if Gb.um_KM:
        if dist.endswith('km'):
            dist = dist.replace('km', ' km')
        else:
            dist = dist.replace('m', ' m')
    else:
        dist = dist.replace('mi', ' mi').replace('ft', ' ft')

    if dist.startswith('0 '):
        dist = dist.replace('0 ', '0.0 ')

    return dist
