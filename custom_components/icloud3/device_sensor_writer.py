#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles the Device HA device_tracker and sensor write methods.
#   They are used by iCloud3_Device.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


from .const             import BATTERY
from .utils.utils       import (instr, is_empty, )
from .utils.messaging   import log_exception

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class DeviceSensorWriterMixin:

    def write_ha_device_tracker_state(self):
        ''' Update the device_tracker entity for this device '''
        if self.DeviceTracker:
            self.DeviceTracker.write_ha_device_tracker_state()

        self._update_restore_state_values()

#--------------------------------------------------------------------
    def write_ha_sensor_state(self, sensor_name, sensor_value):
        '''
        Display a value in a ic3 sensor field

        Input:
            sensor_name     Attribute field name (LOCATED_DATETIME)
            sensor_value    Value that should be displayed (self.loc_data_datetime)
        '''
        if instr(sensor_name, BATTERY) and self.sensors[BATTERY] < 1:
            return

        self.sensors[sensor_name] = sensor_value

        self.write_ha_sensors_state([sensor_name])

#--------------------------------------------------------------------
    def write_ha_sensors_state(self, sensors=None):
        ''' Update the sensors for the Device that are in the sensor_list '''

        try:
            if sensors:
                update_sensors_list = {k:v  for sensor in sensors
                                            for k, v in self.Sensors.items()
                                            if k == sensor}
            else:
                update_sensors_list = self.Sensors.copy()

            update_sensors_list = self._update_battery_sensors(update_sensors_list)

            if is_empty(update_sensors_list):
                return

            for sensor, Sensor in update_sensors_list.items():
                Sensor.write_ha_sensor_state()

            self._update_restore_state_values()

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def write_ha_device_from_zone_sensors_state(self, sensors=None):
        ''' Update the sensors for the Device that are in the sensor_list '''

        if sensors:
            update_sensors_list = {k:v  for sensor in sensors
                                        for k, v in self.Sensors_from_zone.items()
                                        if k.startswith(sensor)}
        else:
            update_sensors_list = self.Sensors_from_zone

        for sensor, Sensor in update_sensors_list.items():
            Sensor.write_ha_sensor_state()

        # rc9 Added update restore state
        self._update_restore_state_values()
