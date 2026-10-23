#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles the Device battery methods. It contains the battery
#   update and display methods used by iCloud3_Device.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


from .global_variables  import GlobalVariables as Gb
from .const             import (STATE, LAST_CHANGED_SECS, LAST_UPDATED_SECS,
                                BATTERY, BATTERY_LEVEL, BATTERY_STATUS, BATTERY_LEVEL_LOW, BADGE,
                                ICLOUD, MOBAPP, PLUS_MINUS, )
from .utils             import entity_io
from .utils.utils       import (instr, is_between, )
from .utils.messaging   import (post_event, log_exception, log_debug_msg, )
from .utils.time_util   import (time_now_secs, secs_to_time, s2t, secs_to_hhmm, )
from .utils.dist_util   import (km_to_um, )

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class DeviceBatteryMixin:

    def update_battery_data_from_mobapp(self):
        '''
        Update the battery info from the Mobile App if the Mobile App data is newer than the iCloud
        battery info. Then update the sensors if it has changed.

        sensor.gary_iphone_app_battery_level entity_attrs={'unit_of_measurement': '%', 'device_class':
            'battery', 'icon': 'mdi:battery-charging-80', 'friendly_name': 'Gary-iPhone-app Battery Level',
            'state': '82', 'last_changed_secs': 1680080444, 'last_changed_time': '5:00:44a'},
        battery_level_attrs={'unit_of_measurement': '%',
            'device_class': 'battery', 'icon': 'mdi:battery-60',
            'friendly_name': 'Gary-iPhone-app Battery Level',
            'last_changed_secs': 1784531678, 'last_changed_time': '3:14:38a',
            'last_updated_secs': 1784531678, 'last_updated_time': '3:14:38a',
            'last_reported_secs': 1784531678, 'last_reported_time': '3:14:38a', 'state': '65'}   |
        sensor.gary_iphone_app_battery_state entity_attrs={'Low Power Mode': False,
            'icon': 'mdi:battery-charging-80', 'friendly_name': 'Gary-iPhone-app Battery State',
            'state': 'charging', 'last_changed_secs': 1680080444, 'last_changed_time': '5:00:44a'}

        Return:
            True - Data has changed
            False - Data has not changed
        '''
        if (self.is_mobapp_monitored is False
                or Gb.conf_data_source_MOBAPP is False
                or self.mobapp.get(BATTERY_LEVEL) is None
                or self.is_dev_data_source_NOT_SET
                or Gb.is_icloud3_startup_inprocess):
            return False

        try:
            battery_level_attrs = entity_io.get_attributes(self.mobapp[BATTERY_LEVEL])
            new_battery_level = int(battery_level_attrs[STATE])
            new_battery_update_secs = \
                max(battery_level_attrs[LAST_UPDATED_SECS],
                    battery_level_attrs[LAST_CHANGED_SECS])

        except Exception as err:
            log_exception(err)
            return False

        if new_battery_level > 99:
            new_battery_status = 'Charged'
        elif instr(battery_level_attrs['icon'], 'charging'):
            new_battery_status = 'Charging'
        elif new_battery_level > 0 and new_battery_level < BATTERY_LEVEL_LOW:
            new_battery_status = 'Low'
        else:
            new_battery_status = 'NotCharging'

        if (new_battery_level == self.mobapp_data_battery_level
                and new_battery_status == self.mobapp_data_battery_status
                and new_battery_update_secs == self.mobapp_data_battery_update_secs):
            return False


        self.mobapp_data_battery_status = new_battery_status

        # Discard mobapp battery info except the status of the info is old
        # if (new_battery_level != self.dev_data_battery_level
        if (self.is_data_source_ICLOUD is False
                and new_battery_update_secs > self.dev_data_battery_update_secs):
            self.mobapp_data_battery_update_secs = new_battery_update_secs
            self.mobapp_data_battery_level       = new_battery_level
            data_source                          = MOBAPP

            log_debug_msg(f"MOBAPP {self.devicename} > MobApp Battery > "
                f"{new_battery_level}, "
                f"Updated-{s2t(new_battery_update_secs)}, "
                f"{new_battery_status}")
        else:
            self.mobapp_data_battery_update_secs = \
                new_battery_update_secs          = self.dev_data_battery_update_secs
            self.mobapp_data_battery_level       = \
                new_battery_level                = self.dev_data_battery_level
            data_source                          = ICLOUD

        self._update_battery_data_and_sensors(
                data_source, new_battery_update_secs, new_battery_level, new_battery_status)

        return True

#-------------------------------------------------------------------
    def _update_battery_data_and_sensors(self, data_source, new_battery_update_secs,
                                                new_battery_level, new_battery_status):
        '''
        Update the dev_data_battery and mobapp_battery fields with the battery data if this
        data is newer
        '''

        if new_battery_level < 1 or new_battery_status == '':
            return

        # with MobApp, Apple reports battery level with 5% adjustment resulting in an
        # incorrect value. Values of 78%-82% report 80%. If so, override with the last value if
        # the last value is +-2 of the current MobApp value.
        self.dev_data_battery_source = self.dev_data_battery_source.replace('*', '')
        if data_source == MOBAPP:
            battery_from = self.dev_data_battery_level - 3
            battery_to   = self.dev_data_battery_level + 3
            if is_between(new_battery_level, battery_from, battery_to):
                new_battery_level   = self.dev_data_battery_level
                data_source     = f"{self.dev_data_battery_source}*"

        self.battery_info[data_source]=(f"{new_battery_level}@{secs_to_time(new_battery_update_secs)}, "
                                                f"{new_battery_status}")

        self.dev_data_battery_update_secs = new_battery_update_secs
        self.dev_data_battery_source      = data_source
        self.dev_data_battery_level       = new_battery_level
        self.dev_data_battery_status      = new_battery_status

        self.write_ha_sensors_state([BATTERY, BATTERY_STATUS, BADGE])

#-------------------------------------------------------------------
    def display_battery_info_msg(self, force_display=False):
        '''
        Display the Battery info msg if the status (Charging, Not Charging) has changed or the
        battery level is divisible by 5 (80, 85, etc.)
        '''

        # Return if it hasn't been set up yet
        if self.dev_data_battery_update_secs == 0:
            return False

        if self.last_battery_msg_time == secs_to_hhmm(self.dev_data_battery_update_secs):
            return

        # if (self.dev_data_battery_level != self.dev_data_battery_level_last
        #         or self.dev_data_battery_status != self.dev_data_battery_status_last):
        #     force_display = True

        mobapp_msg = f" ({PLUS_MINUS}2%)" if self.dev_data_battery_source == MOBAPP else ''
        battery_msg = f"{self.dev_data_battery_level}%{mobapp_msg}, {self.format_battery_status}"

        # if force_display is True:
        #     pass
        # elif battery_msg == self.last_battery_msg:
        #     return
        if battery_msg == self.last_battery_msg:
            return

        if self.is_tracked:
            loc_msg = ''
        elif self.isin_zone and self.isnotin_statzone:
            loc_msg = f"{self.loc_data_zone_fname}, "
        elif self.FromZone_Home and self.FromZone_Home.zone_dist_km > 0:
            loc_msg = f"Home-{(km_to_um(self.FromZone_Home.zone_dist_km))}, "
        else:
            loc_msg = ''

        post_event(self.devicename,
                f"{loc_msg}"
                f"Battery > {battery_msg} ({self.dev_data_battery_source}), "
                f"Updated {secs_to_hhmm(self.dev_data_battery_update_secs)}")

        if Gb.EvLog.evlog_attrs['selected_dname'] == self.devicename:
            Gb.EvLog.update_event_log_display(self.devicename)

        # self.dev_data_battery_level_last  = self.dev_data_battery_level
        # self.dev_data_battery_status_last = self.dev_data_battery_status
        self.last_battery_msg_time        = secs_to_hhmm(self.dev_data_battery_update_secs)
        self.last_battery_msg             = battery_msg
        self.last_battery_msg_secs        = time_now_secs()

        return True
