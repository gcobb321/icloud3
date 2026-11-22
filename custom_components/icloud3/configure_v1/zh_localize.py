"""Translate configuration option labels without changing their stored values.

The selectors contain English values used by iCloud3 for routing. Only the
labels are localized, and unsupported languages keep the upstream labels.
"""

import json
import re
from pathlib import Path

from homeassistant.helpers import selector
from homeassistant.helpers import config_validation as cv
from ..global_variables import GlobalVariables as Gb


_LABELS = {
    language: json.loads(Path(__file__).with_name(
        f'zh_selector_labels_{language}.json').read_text(encoding='utf-8'))
    for language in ('zh-Hans', 'zh-Hant')
}
_DYNAMIC_TEMPLATES = {}
for _language, _labels in _LABELS.items():
    _DYNAMIC_TEMPLATES[_language] = []
    for _value, _label in _labels.items():
        for _marker in ('^add-text^', '^otp_msg', '{method_info}'):
            if _marker in _value and _marker in _label:
                _left, _right = _value.split(_marker, 1)
                _DYNAMIC_TEMPLATES[_language].append(
                    (re.compile('^'+re.escape(_left)+'(.*?)'+re.escape(_right)+'$', re.S),
                     _label, _marker))

_DYNAMIC_PHRASES = {
    'AUTH NEEDED': '需要验证',
    'TERMS-OF-USE APPROVAL NEEDED': '需要接受使用条款',
    'APPLE REFUSED RQST-503': 'Apple 拒绝请求（503）',
    'LOGIN FAILED': '登录失败',
    'Devices Tracked': '台设备已跟踪',
}


def _language():
    """Home Assistant runs config flows on the server, using its language."""
    hass = Gb.hass
    language = getattr(getattr(hass, 'config', None), 'language', '')
    if language in ('zh-Hans', 'zh_CN', 'zh-CN', 'zh'):
        return 'zh-Hans'
    if language in ('zh-Hant', 'zh_TW', 'zh-TW', 'zh_HK', 'zh-HK'):
        return 'zh-Hant'
    return None


def _display_label(value):
    language = _language()
    if language is None:
        return value
    labels = _LABELS[language]
    label = labels.get(value)
    if label is not None:
        return label
    if value.startswith('HA Zone Friendly Name (') and value.endswith(' → PREFERRED'):
        name = value[len('HA Zone Friendly Name ('):-len(') → PREFERRED')]
        return (f'HA 區域顯示名稱（{name}，建議）' if language == 'zh-Hant'
                else f'HA 区域显示名称（{name}，推荐）')
    if value.startswith('HA Zone entity_id (') and value.endswith(')'):
        name = value[len('HA Zone entity_id ('):-1]
        return (f'HA 區域實體 ID（{name}）' if language == 'zh-Hant'
                else f'HA 区域实体 ID（{name}）')
    if value.startswith('iCloud3 reformated Zone entity_id (') and value.endswith(')'):
        name = value[len('iCloud3 reformated Zone entity_id ('):-1]
        return (f'iCloud3 格式化區域實體 ID（{name}）' if language == 'zh-Hant'
                else f'iCloud3 格式化区域实体 ID（{name}）')
    for pattern, template, marker in _DYNAMIC_TEMPLATES[language]:
        match = pattern.fullmatch(value)
        if match:
            return template.replace(marker, match.group(1))
    label = re.sub(r'(\d+) of (\d+) Devices Tracked',
                   lambda match: (f'已追蹤 {match.group(1)}/{match.group(2)} 部裝置'
                                  if language == 'zh-Hant' else
                                  f'已跟踪 {match.group(1)}/{match.group(2)} 台设备'),
                   value)
    for original, chinese in _DYNAMIC_PHRASES.items():
        label = label.replace(original, _traditional(chinese) if language == 'zh-Hant' else chinese)
    return label


def _traditional(text):
    """Translate the few dynamic phrases that do not come from the JSON file."""
    return {
        '需要验证': '需要驗證', '需要接受使用条款': '需要接受使用條款',
        'Apple 拒绝请求（503）': 'Apple 拒絕請求（503）',
        '登录失败': '登入失敗', '台设备已跟踪': '部裝置已追蹤',
    }.get(text, text)


def localized_select_selector_config(*, options, **kwargs):
    labeled = []
    for option in options:
        if isinstance(option, str):
            label = _display_label(option)
            labeled.append({'value': option, 'label': label})
        elif isinstance(option, dict) and isinstance(option.get('label'), str):
            labeled.append({**option, 'label': _display_label(option['label'])})
        else:
            labeled.append(option)
    return selector.SelectSelectorConfig(options=labeled, **kwargs)


def localized_multi_select(options):
    if isinstance(options, dict):
        labeled = {value: _display_label(label) if isinstance(label, str) else label
                   for value, label in options.items()}
    else:
        labeled = {value: _display_label(value) if isinstance(value, str) else value
                   for value in options}
    return cv.multi_select(labeled)
