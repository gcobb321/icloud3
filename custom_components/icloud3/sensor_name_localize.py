"""Display-only names for legacy iCloud3 sensors.

The English sensor definitions are also used by configuration screens and
saved exclusion lists. Keep those names and all entity identifiers unchanged.
"""

_NAMES = {
    'Name': ('名称', '名稱'),
    'Badge': ('徽章', '徽章'),
    'Battery': ('电量', '電量'),
    'BatteryStatus': ('电池状态', '電池狀態'),
    'Info': ('信息', '資訊'),
    'Interval': ('更新间隔', '更新間隔'),
    'LastLocated': ('上次定位', '上次定位'),
    'LastUpdate': ('上次更新', '上次更新'),
    'NextUpdate': ('下次更新', '下次更新'),
    'TravelTime': ('行程时间', '行程時間'),
    'TravelTime (min)': ('行程时间（分钟）', '行程時間（分鐘）'),
    'TravelTime (hh:mm)': ('行程时间（时:分）', '行程時間（時:分）'),
    'TravelTimeMin': ('行程时间（分钟）', '行程時間（分鐘）'),
    'ArrivalTime': ('到达时间', '抵達時間'),
    'ZoneDistance': ('到区域距离', '到區域距離'),
    'HomeDistance': ('到家距离', '到家距離'),
    'Distance': ('距离', '距離'),
    'Direction': ('移动方向', '移動方向'),
    'MovedDistance': ('移动距离', '移動距離'),
    'ZoneInfo': ('区域信息', '區域資訊'),
    'Trigger': ('触发原因', '觸發原因'),
    'WazeDistance': ('Waze 路线距离', 'Waze 路線距離'),
    'CalcDistance': ('计算距离', '計算距離'),
    'Zone': ('区域', '區域'),
    'ZoneFname': ('区域显示名', '區域顯示名稱'),
    'ZoneName': ('区域名称', '區域名稱'),
    'ZoneChanged': ('区域变更时间', '區域變更時間'),
    'LastZone': ('上个区域', '上一個區域'),
    'GPSAccuracy': ('GPS 精度', 'GPS 精度'),
    'Altitude': ('海拔', '海拔'),
    'VerticalAccuracy': ('垂直精度', '垂直精度'),
    'iCloud3 Event Log': ('iCloud3 事件日志', 'iCloud3 事件日誌'),
    'iCloud3 Alerts': ('iCloud3 提醒', 'iCloud3 提醒'),
    'iCloud3 Waze History Track': ('iCloud3 Waze 历史轨迹', 'iCloud3 Waze 歷史軌跡'),
}


def localized_sensor_name(english_name, hass):
    """Return a name in the HA server language, leaving unknown names intact."""
    language = getattr(getattr(hass, 'config', None), 'language', '') or ''
    language = language.replace('_', '-').lower()
    names = _NAMES.get(english_name)
    if names is None:
        return english_name
    if language in ('zh-hant', 'zh-tw', 'zh-hk', 'zh-mo'):
        return names[1]
    if language in ('zh-hans', 'zh-cn', 'zh'):
        return names[0]
    return english_name
