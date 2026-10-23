#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles the Device restore state methods. It contains the
#   restore state save/reset methods used by iCloud3_Device.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


from .global_variables       import GlobalVariables as Gb
from .const                  import (ZONE_ENTER_SECS, ZONE_EXIT_SECS, LAST_ZONE_NAME,
                                     BATTERY, BATTERY_STATUS, BATTERY_SOURCE,
                                     DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                     HHMMSS_ZERO, ALERT)
from .startup                import restore_state
from .utils.time_util        import datetime_now
from .utils.utils            import is_running_in_event_loop
from .utils.messaging        import log_debug_msg, log_exception
import copy

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class DeviceRestoreMixin:

    def _update_restore_state_values(self):
        """ Save the Device's updated sensors in the icloud3.restore_state file """

        if (self.can_update_sensors is False
                or is_running_in_event_loop()):
            return

        Gb.restore_state_devices[self.devicename] = {}
        Gb.restore_state_devices[self.devicename]['last_update'] = datetime_now()
        Gb.restore_state_devices[self.devicename]['sensors']     = copy.deepcopy(self.sensors)
        Gb.restore_state_devices[self.devicename]['mobapp']      = self._restore_state_save_mobapp_items()
        Gb.restore_state_devices[self.devicename]['other']       = self._restore_state_save_other_items()

        Gb.restore_state_devices[self.devicename]['from_zone'] = {}
        for from_zone, FromZone in self.FromZones_by_zone.items():
            Gb.restore_state_devices[self.devicename]['from_zone'][from_zone] = copy.deepcopy(FromZone.sensors)

        restore_state.write_icloud3_restore_state_file()

#--------------------------------------------------------------------
    def _restore_state_save_mobapp_items(self):
        '''
        Build dictionary of Mobile App items to be saved in restore_state file
        '''
        mobapp_items = {}
        mobapp_items['state']          = self.mobapp_data_state
        mobapp_items['latitude']       = self.mobapp_data_latitude
        mobapp_items['longitude']      = self.mobapp_data_longitude
        mobapp_items['source_type']    = self.mobapp_data_source_type
        mobapp_items['state_secs']     = self.mobapp_data_state_secs
        mobapp_items['state_time']     = self.mobapp_data_state_time
        mobapp_items['trigger_secs']   = self.mobapp_data_trigger_secs
        mobapp_items['trigger_time']   = self.mobapp_data_trigger_time
        mobapp_items['secs']           = self.mobapp_data_secs
        mobapp_items['time']           = self.mobapp_data_time
        mobapp_items['trigger']        = self.mobapp_data_trigger
        mobapp_items['battery_level']  = self.mobapp_data_battery_level
        mobapp_items['battery_status'] = self.mobapp_data_battery_status
        mobapp_items['battery_update_secs'] = self.mobapp_data_battery_update_secs
        return mobapp_items


#--------------------------------------------------------------------
    def _restore_state_reset_mobapp_items(self):

        try:
            mobapp_items = Gb.restore_state_devices[self.devicename]['mobapp']

            self.mobapp_data_state          = mobapp_items['state']
            self.mobapp_data_latitude       = mobapp_items['latitude']
            self.mobapp_data_longitude      = mobapp_items['longitude']
            self.mobapp_data_source_type    = mobapp_items['source_type']
            self.mobapp_data_state_secs     = mobapp_items['state_secs']
            self.mobapp_data_state_time     = mobapp_items['state_time']
            self.mobapp_data_trigger_secs   = mobapp_items['trigger_secs']
            self.mobapp_data_trigger_time   = mobapp_items['trigger_time']
            self.mobapp_data_secs           = mobapp_items['secs']
            self.mobapp_data_time           = mobapp_items['time']
            self.mobapp_data_trigger        = mobapp_items['trigger']
            self.mobapp_data_battery_level  = mobapp_items['battery_level']
            self.mobapp_data_battery_status = mobapp_items['battery_status']
            self.mobapp_data_battery_update_secs =  mobapp_items['battery_update_secs']

        except Exception as err:
            log_debug_msg(f"_restore_state_reset_mobapp_items > {type(err).__name__}")

#--------------------------------------------------------------------
    def _restore_state_save_other_items(self):
        '''
        Build dictionary of Otheritems to be saved in restore_state file
        '''
        other_items = {
            'zone': self.loc_data_zone,
            'zone_change_secs': self.zone_change_secs,
            'zone_change_datetime': self.zone_change_datetime
        }

        return other_items

#--------------------------------------------------------------------
    def restore_state_reset_other_items(self):

        try:

            device_items = Gb.restore_state_devices[self.devicename]
            if 'other' in device_items:
                other_items = device_items['other']
                if other_items.get('zone', '') == self.loc_data_zone:
                    self.zone_change_secs     = other_items['zone_change_secs']
                    self.zone_change_datetime = other_items['zone_change_datetime']

            self.zone_enter_secs = self.sensors[ZONE_ENTER_SECS]
            self.zone_exit_secs  = self.sensors[ZONE_EXIT_SECS]
            self.last_zone       = self.sensors[LAST_ZONE_NAME]
            self.dev_data_battery_level  = self.sensors[BATTERY]
            self.dev_data_battery_status = self.sensors[BATTERY_STATUS]
            self.dev_data_battery_source = self.sensors[BATTERY_SOURCE]

            self.sensors[DISTANCE_TO_OTHER_DEVICES] = {}
            self.sensors[DISTANCE_TO_OTHER_DEVICES_DATETIME] = HHMMSS_ZERO
            self.sensors[ALERT] = ''


        except Exception as err:
            log_exception(err)
            pass
