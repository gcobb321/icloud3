"""Localize generated dashboard text without changing entity IDs or user names."""

DASHBOARD_TEXT_ZH_HANS = {
    "Main": "主页",
    "Other Devices": "其他设备",
    "*All Info": "*全部信息",
    "*Track Results": "*追踪结果",
    "*Badge, Battery": "*徽章与电量",
    "Event Log": "事件日志",
    "Main (Backup)": "主页（备份）",
    "Main Screen - Before Last Recreate Action": "上次重建前的主页",
    "Arrive": "到达时间",
    "Distance": "距离",
    "TravTime": "行程时间",
    "NextUpdt": "下次更新",
    "Battery": "电量",
    "Interval": "更新间隔",
    "Moved": "移动距离",
    "Located": "定位时间",
    "LastUpdt": "上次更新",
    "<br><h3>Device Badge Sensors</h3>": "<br><h3>设备徽章传感器</h3>",
    "<br><h3>Device Battery Sensors</h3>": "<br><h3>设备电量传感器</h3>",
    "<h4><br>🀫 Combined Group (results+status+info) → ^fname</h4>": "<h4><br>🀫 合并分组（结果+状态+信息）→ ^fname</h4>",
    "<h4><br>[Ⲷ] Separate Groups (results, status, info) → ^fname</h4>": "<h4><br>[Ⲷ] 独立分组（结果、状态、信息）→ ^fname</h4>",
    "<h3>Device Information (Tracking Results & Status, Device Info Msg)</h3>This screen shows Device Information sensors that can be copied and pasted to other dashboards as a combined group or as group sections.": "<h3>设备信息（追踪结果、状态及消息）</h3>此页面展示设备信息传感器，可按合并分组或独立分组复制到其他仪表盘。",
    "<h3>Device Information - Tracking Results</h3>This screen shows the Tracking Results group for all devices.": "<h3>设备信息 - 追踪结果</h3>此页面展示所有设备的追踪结果分组。",
    "<h3>Device Badge and Battery Sensors</h3>This screen shows t,he Device’s Badge and Battery sensors in several formats that can be copied and pasted to other dashboards": "<h3>设备徽章与电量传感器</h3>此页面以多种格式展示徽章和电量传感器，可复制到其他仪表盘。",
    "<h3>Device Battery Sensors</h3>This screen shows the Device’s Battery sensors in several formats that can be copied and pasted to other dashboards": "<h3>设备电量传感器</h3>此页面以多种格式展示电量传感器，可复制到其他仪表盘。"
}

def dashboard_text(text, language):
    """Translate built-in labels for Simplified Chinese; retain other languages."""
    if language in ("zh-Hans", "zh-CN", "zh", "zh-cn"):
        return DASHBOARD_TEXT_ZH_HANS.get(text, text)
    return text


def localize_template(value, language):
    """Return a localized copy before device names are substituted into templates."""
    if isinstance(value, dict):
        return {key: localize_template(item, language) for key, item in value.items()}
    if isinstance(value, list):
        return [localize_template(item, language) for item in value]
    if isinstance(value, str):
        return dashboard_text(value, language)
    return value
