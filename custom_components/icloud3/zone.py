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
                                STATZONE_RADIUS_1M,
                                ZONE, NON_ZONE_ITEM_LIST, )

from .utils             import entity_io
from .utils.utils       import (instr, is_statzone, format_gps, zone_dname,
                                list_add, list_del, )
from .utils.messaging   import (post_event, post_error_msg, post_monitor_msg,
                                log_exception, log_data,_evlog, _log, )
from .utils.time_util   import (time_now_secs, )
from .utils.dist_util   import (gps_distance_m, gps_distance_km, )


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

    def __init__(self, zone, zone_data=None):
        self.zone = zone.replace('zone.', '')
        self.zone_data = {} if zone_data is None else zone_data

        self.zone_entity_id   = f"zone.{zone}"
        self.ha_zone_attrs    = None
        self.ha_zone_attrs_id = 0
        self.is_ha_zone       = self.zone_data.get('ha_zone', True) and zone not in NON_ZONE_ITEM_LIST
        self.status           = 1 if self.is_ha_zone else 0    # changed to -1 when removed from HA
        self.dist_time_history= []   # Entries are a list - [lat, long, distance, travel time]

        self.initialize_zone_name(self.zone_data)
        self.setup_zone_display_name()

        list_add(Gb.Zones, self)
        Gb.Zones_by_zone[zone] = self

        if self.is_ha_zone:
            list_add(Gb.HAZones, self)
            Gb.HAZones_by_zone[self.zone] = self

        if zone_data:
            log_data(f"Zone Data - <{zone} > ", self.zone_data, log_data_flag=True)
        if self.ha_zone_attrs:
            log_data(f"Zone Attrs - <{zone} > ", self.ha_zone_attrs, log_data_flag=True)

        if zone == HOME:
            Gb.HomeZone = self

    def __repr__(self):
        return (f"<Zone: {self.zone}>")

    #---------------------------------------------------------------------
    def update_zone_config(self, force_update=False):
        '''
        Check to see if the zone configuration was changed on the Settings >
        Devices & services > Areas & Zones > Zones screen by comparing the
        id(zone-attributes) with the one saved when the zone was set up.
        If they are different, update the zone lat, long, radius, passive & name
        with the new values.
        '''
        if self.is_ha_zone is False:
            return
        elif force_update:
            pass
        elif self.ha_zone_attrs_id == entity_io.ha_zone_attrs_id(self.zone):
            return

        ha_zone_attrs = entity_io.ha_zone_attrs(self.zone)

        if ha_zone_attrs and LATITUDE not in ha_zone_attrs:
            return

        if self not in Gb.HAZones:
            Gb.HAZones.append(self)
            Gb.HAZones_by_zone[self.zone] = self

        self.ha_zone_attrs    = ha_zone_attrs
        self.ha_zone_attrs_id = id(ha_zone_attrs)

    #---------------------------------------------------------------------
    @property
    def ha_fname(self):
        try:
            return Gb.hass.states.get(self.zone_entity_id).attributes[FRIENDLY_NAME]
        except:
            return self.zone.title()

    #---------------------------------------------------------------------
    @property
    def latitude(self):
        try:
            if self.is_ha_zone:
                if self.fname != self.ha_fname:
                    self.fname = self.ha_fname
                    self.setup_zone_display_name()

                return Gb.hass.states.get(self.zone_entity_id).attributes[LATITUDE]
            else:
                return self.zone_data.get(LATITUDE, 0)
        except:
            return 0

    #---------------------------------------------------------------------
    @property
    def longitude(self):
        try:
            if self.is_ha_zone:
                return Gb.hass.states.get(self.zone_entity_id).attributes[LONGITUDE]
            else:
                return self.zone_data.get(LONGITUDE, 0)
        except:
            return 0

    #---------------------------------------------------------------------
    @property
    def radius_m(self):
        try:
            if self.is_ha_zone:
                return int(Gb.hass.states.get(self.zone_entity_id).attributes[RADIUS])
            else:
                return self.zone_data.get(RADIUS, 0)
        except:
            return 0

    #---------------------------------------------------------------------
    @property
    def passive(self):
        try:
            if self.is_ha_zone:
                return Gb.hass.states.get(self.zone_entity_id).attributes[PASSIVE]
            else:
                return self.zone_data.get(PASSIVE, True)
        except:
            return True

    #---------------------------------------------------------------------
    def initialize_zone_name(self, zone_data=None):

        ztitle = self.zone.title().replace("_S_","'s " ).replace("_", " ")
        ztitle = ztitle.replace(' Iphone', ' iPhone')
        ztitle = ztitle.replace(' Ipad', ' iPad')
        ztitle = ztitle.replace(' Ipod', ' iPod')

        self.title = ztitle
        self.name  = ztitle.replace(" ","").replace("'", "`")

        if self.is_ha_zone:
            self.dname = self.fname = self.ha_fname
        elif zone_data:
            self.dname = self.fname = zone_data.get(FRIENDLY_NAME, self.zone.title())
        elif self.zone in Gb.zones_dname:
            self.dname = self.fname = zone_dname(self.zone)
        else:
            self.dname = self.fname = self.zone.title()

    #---------------------------------------------------------------------
    def setup_zone_display_name(self):
        '''
        Set the zone display_as field using the config display_as format value
        '''
        if self.is_ha_zone:
            if Gb.display_zone_format == ZONE:
                self.dname = self.zone
            elif Gb.display_zone_format == FNAME:
                self.dname = self.fname
            elif Gb.display_zone_format == NAME:
                self.dname = self.name
            elif Gb.display_zone_format == TITLE:
                self.dname = self.title
            else:
                self.dname = self.fname
        elif self.zone in Gb.zones_dname:
            return

        self.names = [self.zone, self.dname]

        Gb.zones_dname[self.zone]  = self.dname
        Gb.zones_dname[self.fname] = self.dname
        Gb.zones_dname[self.name]  = self.dname
        Gb.zones_dname[self.title] = self.dname

        self.sensor_prefix = '' if self.zone == HOME else self.dname

        # Used in entity_io to change Mobile App state value to the actual zone entity name for internal use
        Gb.state_to_zone[self.fname] = self.zone
        Gb.state_to_zone[self.dname] = self.zone

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
        distance = gps_distance_m(self.gps, to_gps)
        distance = 0 if distance < .002 else distance
        return distance

    # Calculate distance in kilometers
    def distance_km(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        distance = gps_distance_km(self.gps, to_gps)
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
        statzone_id      = statzone_id.replace(f"ic3_{STATIONARY}_", "")
        self.zone        = f"ic3_{STATIONARY}_{statzone_id}"
        self.statzone_id = statzone_id
        self.setup_time_secs = time_now_secs()

        self.removed_from_ha_secs = HIGH_INTEGER

        self.fname = f"StatZon{self.statzone_id}"
        self.fname_id = self.dname = Gb.zones_dname[self.zone] = self.fname

        self.initialize_statzone_name()
        self.initialize_zone_attrs()

        statzone_data ={FRIENDLY_NAME: self.fname,
                        FNAME: self.fname,
                        LATITUDE: self.zero_latitude,
                        LONGITUDE: self.zero_longitude,
                        RADIUS: STATZONE_RADIUS_1M,
                        PASSIVE: True}

        super().__init__(self.zone, zone_data=statzone_data)

        self.write_ha_zone_state(self.passive_attrs)

        self.name = self.title = self.dname

#--------------------------------------------------------------------
    def initialize_statzone_name(self):
        if Gb.statzone_fname == '': Gb.statzone_fname = 'StatZon#'
        self.fname = Gb.statzone_fname.replace('#', self.statzone_id)
        self.fname_id = self.dname = Gb.zones_dname[self.zone] = self.fname

        if instr(Gb.statzone_fname, '#') is False:
            self.fname_id = f"{self.fname} (..._{self.statzone_id})"

        self.zero_latitude = self.zero_longitude = 0

#--------------------------------------------------------------------
    def initialize_zone_attrs(self):
        # base_attrs is used to set up the stationary zone and to reset it to passive

        self.attrs            = {}
        self.attrs[NAME]      = self.zone
        self.attrs[FRIENDLY_NAME] = self.fname
        self.attrs[LATITUDE]  = self.zero_latitude
        self.attrs[LONGITUDE] = self.zero_longitude
        self.attrs[RADIUS]    = Gb.statzone_radius_m
        self.attrs[PASSIVE]   = False

        statzone_num = int(self.statzone_id)
        if statzone_num < 10:
            self.attrs[ICON] = f"mdi:numeric-{statzone_num}-circle-outline"
        elif statzone_num < 20:
            self.attrs[ICON] = f"mdi:numeric-{statzone_num-10}-box-outline"
        elif statzone_num < 30:
            self.attrs[ICON] = f"mdi:numeric-{statzone_num-20}-circle"
        elif statzone_num < 40:
            self.attrs[ICON] = f"mdi:numeric-{statzone_num-30}-box"
        else:
            self.attrs[ICON] = f"mdi:numeric-9-plus-circle-outline"

        # passive_attrs is used to set the stationary zone  location and make it useable
        self.passive_attrs          = self.attrs.copy()
        self.passive_attrs[RADIUS]  = STATZONE_RADIUS_1M
        self.passive_attrs[PASSIVE] = True

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

    @property
    def is_small_statzone(self):
        return self.radius_m != Gb.statzone_radius_m

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
