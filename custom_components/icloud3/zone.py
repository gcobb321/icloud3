#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles all tracking activities for a device. It contains
#   the following modules:
#       TrackFromZones - iCloud3 creates an object for each device/zone
#           with the tracking data fields.
#
#   The primary methods are:
#       determine_interval - Determines the polling interval, update times,
#           location data, etc for the device based on the distance from
#           the zone.
#       determine_interval_after_error - Determines the interval when the
#           location data is to be discarded due to poor GPS, it is old or
#           some other error occurs.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from .global_variables  import GlobalVariables as Gb
from .const             import (HOME, NOT_HOME, STATIONARY, HIGH_INTEGER,
                                ZONE, TITLE, FNAME, NAME, ID, FRIENDLY_NAME, ICON,
                                LATITUDE, LONGITUDE, RADIUS, PASSIVE,
                                STATZONE_RADIUS_1M, ZONE, )
from .support           import iosapp_interface
from .helpers.common    import (instr, is_statzone, format_gps, zone_display_as,)
from .helpers.messaging import (post_event, post_error_msg, post_monitor_msg,
                                log_exception, log_rawdata,_trace, _traceha, )
from .helpers.time_util import (time_now_secs, datetime_now, secs_to_time, secs_since,
                                secs_to_datetime, format_time_age, )
from .helpers.dist_util import (calc_distance_m, calc_distance_km, format_dist_km, format_dist_m, )


MDI_NAME_LETTERS = {'circle-outline': '', 'box-outline': '', 'circle': '', 'box': ''}


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Zones Class Object
#       Set up the object for each Zone.
#
#       Input:
#           zone - Zone name
#           zone_data - A dictionary containing the Zone attributes
#                   (latitude, longitude. radius, passive, friendly name)
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_Zone(object):

    def __init__(self, zone, zone_data):
        self.zone = zone

        if NAME in zone_data:
            ztitle = zone_data[NAME].title()
        else:
            ztitle = zone.title().replace("_S_","'s " ).replace("_", " ")
            ztitle = ztitle.replace(' Iphone', ' iPhone')
            ztitle = ztitle.replace(' Ipad', ' iPad')
            ztitle = ztitle.replace(' Ipod', ' iPod')

        self.fname      = zone_data.get(FRIENDLY_NAME, ztitle)      # From zones_states attribute (zones config file)
        self.display_as = self.fname

        self.name       = ztitle.replace(" ","").replace("'", "`")
        self.title      = ztitle

        # contains the statzone names to easily determine if a device's zone name is this stat zone
        self.names      = [self.zone, self.display_as]

        self.latitude   = zone_data.get(LATITUDE, 0)
        self.longitude  = zone_data.get(LONGITUDE, 0)
        self.radius_m   = round(zone_data.get(RADIUS, 100))
        self.passive    = zone_data.get(PASSIVE, True)
        self.is_real_zone    = (self.radius_m > 0)
        self.isnot_real_zone = not self.is_real_zone    # (Description only zones/Away, not_home, not_set, etc)
        self.dist_time_history = []                     # Entries are a list - [lat, long, distance, travel time]

        self.er_zone_id = zone_data.get(ID, zone.lower())     # HA entity_registry id
        self.entity_id  = self.er_zone_id[:6]
        self.unique_id  = zone_data.get('unique_id', zone.lower())

        self.setup_zone_display_name()

        log_rawdata(f"Zone Data - <{zone} > ", zone_data, log_rawdata_flag=True)

        if zone == HOME:
            Gb.HomeZone = self

    def __repr__(self):
        return (f"<Zone: {self.zone}>")

    #---------------------------------------------------------------------
    def setup_zone_display_name(self):
        '''
        Set the zone display_as field using the config display_as format value
        '''
        if Gb.display_zone_format   == ZONE:
            self.display_as = self.zone
        elif Gb.display_zone_format == FNAME:
            self.display_as = self.fname
        elif Gb.display_zone_format == NAME:
            self.display_as = self.name
        elif Gb.display_zone_format == TITLE:
            self.display_as = self.title
        else:
            self.display_as = self.fname

        self.names = [self.zone, self.display_as]

        Gb.zone_display_as[self.zone]  = self.display_as
        Gb.zone_display_as[self.fname] = self.display_as
        Gb.zone_display_as[self.name]  = self.display_as
        Gb.zone_display_as[self.title] = self.display_as

        self.sensor_prefix = '' if self.zone == HOME else self.display_as

        # Used in entity_io to change ios app state value to the actual zone entity name for internal use
        Gb.state_to_zone[self.fname]      = self.zone
        Gb.state_to_zone[self.display_as] = self.zone

    #---------------------------------------------------------------------
    @property
    def is_statzone(self):
        return instr(self.zone, STATIONARY)

    @property
    def isnot_statzone(self):
        return instr(self.zone, STATIONARY) is False

    def is_my_statzone(self, Device):
        return self.zone == f"{Device.devicename}_{STATIONARY}"

    @property
    def gps(self):
        return (self.latitude, self.longitude)

    @property
    def latitude5(self):
        return round(self.latitude, 5)

    @property
    def longitude5(self):
        return round(self.longitude, 5)

    @property
    def radius_km(self):
        return round(self.radius_m/1000, 4)

    # Calculate distance in meters
    def distance_m(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        distance = calc_distance_m(self.gps, to_gps)
        distance = 0 if distance < .002 else distance
        return distance

    # Calculate distance in kilometers
    def distance_km(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        distance = calc_distance_km(self.gps, to_gps)
        distance = 0 if distance < .00002 else distance
        return distance

    # Return the DeviceFmZone obj from the devicename and this zone
    @property
    def FromZone(self, Device):
        return (f"{Device.devicename}:{self.zone}")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   StationaryZones Class Object
#       Set up the Stationary Zone for each device. Then add the Stationary Zone
#       To the Zones Class Object.
#
#       Input:
#           device - Device's name
#
#        Methods:
#           attrs - Return the attributes for the Stat Zone to be used to update the HA Zone entity
#           time_left - The time left until the phone goes into a Stat Zone
#           update_dist(dist) - Add the 'dist' to the moved_dist
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_StationaryZone(iCloud3_Zone):

    def __init__(self, statzone_id):
        self.zone        = f"ic3_{STATIONARY}_{statzone_id}"
        self.statzone_id = statzone_id

        self.removed_from_ha_secs = HIGH_INTEGER

        self.base_attrs = {}
        self.fname = f"StatZon{self.statzone_id}"
        self.fname_id = self.display_as = Gb.zone_display_as[self.zone] = self.fname

        # base_attrs is used to move the stationary zone back to it's base
        self.base_attrs[NAME]    = self.zone
        self.base_attrs[RADIUS]  = STATZONE_RADIUS_1M
        self.base_attrs[PASSIVE] = True

        statzone_num = int(statzone_id)
        if statzone_num < 10:
            self.base_attrs[ICON] = f"mdi:numeric-{statzone_num}-circle-outline"
        elif statzone_num < 20:
            self.base_attrs[ICON] = f"mdi:numeric-{statzone_num-10}-box-outline"
        elif statzone_num < 30:
            self.base_attrs[ICON] = f"mdi:numeric-{statzone_num-20}-circle"
        elif statzone_num < 40:
            self.base_attrs[ICON] = f"mdi:numeric-{statzone_num-30}-box"
        else:
            self.base_attrs[ICON] = f"mdi:numeric-9-plus-circle-outline"

        self.initialize_updatable_items()

        statzone_data ={FRIENDLY_NAME: self.fname,
                        LATITUDE: self.base_latitude,
                        LONGITUDE: self.base_longitude,
                        RADIUS: STATZONE_RADIUS_1M, PASSIVE: True}


        # Initialize Zone with location
        super().__init__(self.zone, statzone_data)
        self.write_ha_zone_state(self.base_attrs)
        self.name = self.title = self.display_as

        # away_attrs is used to move the stationary zone back to it's base
        self.away_attrs = self.base_attrs.copy()
        self.away_attrs[RADIUS]        = Gb.statzone_radius_m
        self.away_attrs[PASSIVE]       = False

#--------------------------------------------------------------------
    def initialize_updatable_items(self):
        if Gb.statzone_fname == '': Gb.statzone_fname = 'StatZon#'
        self.fname = Gb.statzone_fname.replace('#', self.statzone_id)
        self.fname_id = self.display_as = Gb.zone_display_as[self.zone] = self.fname
        if instr(Gb.statzone_fname, '#') is False:
            self.fname_id = f"{self.fname} (..._{self.statzone_id})"

        self.base_latitude  = 0
        self.base_longitude = 0

        self.base_attrs[FRIENDLY_NAME] = self.fname
        self.base_attrs[LATITUDE]      = self.base_latitude
        self.base_attrs[LONGITUDE]     = self.base_longitude

#--------------------------------------------------------------------
    def __repr__(self):
        return (f"<StatZone: {self.zone}>")

#---------------------------------------------------------------------
    # Return True if the device has not set up a Stationary Zone
    @property
    def is_at_base(self):
        return self.passive

    # Return True if the device has set up a Stat Zone
    @property
    def isnot_at_base(self):
        return self.passive is False

    @property
    def device_distance_m(self):
        return self.distance_m(self.Device.loc_data_latitude, self.Device.loc_data_longitude)

    # Return the attributes for the Stat Zone to be used to update the HA Zone entity
    @property
    def attrs(self):
        _attrs = self.base_attrs
        _attrs[LATITUDE]  = self.latitude
        _attrs[LONGITUDE] = self.longitude
        _attrs[RADIUS]    = self.radius_m

        return _attrs

#--------------------------------------------------------------------
    def write_ha_zone_state(self, attrs):
        '''
        Update the zone entity with the new attributes (lat/long, passive, radius, etc)
        '''
        try:
            Gb.hass.states.async_set(f"zone.{self.zone}", 0, attrs, force_update=True)

        except Exception as err:
            pass
            # log_exception(err)

#--------------------------------------------------------------------
    def remove_ha_zone(self):
        '''
        Remove the zone entity from HA when there are no Devices in it
        '''

        try:
            Gb.hass.states.async_remove(f"zone.{self.zone}")
            Gb.hass.services.call(ZONE, "reload")

            post_event(f"Removed HA Zone > {self.fname_id}")

        except Exception as err:
            # log_exception(err)
            pass

#--------------------------------------------------------------------
