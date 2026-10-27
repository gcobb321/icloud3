'''
Convert an Apple device name into a suggested iCloud3 fname ("Gary's iPhone" ->
"Gary-iPhone"). It is used to suggest the fname when devices are imported from the
Apple acct and to recognize a replacement device that was given the Apple default
name ("Lillian's Apple Watch" and "Lillian-Watch" are both "Lillian-Watch").

This module does not import any iCloud3 modules so it can be used by the Apple acct
device modules and by the config flow.

CathiPad 11 => Cath-iPad_ic3
CathiPad 13 => Cath-iPad
CathiPhone is correct
KenniPad 11 => Kenn-iPad
KenniPad 13 => Kenn-iPad_ic3
KenniPhone is correct
KenniWatch2 => Kenni-Watch
KenniWatch11 is correct

KenniWatch7 is missing

'''
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            CONVERT APPLE DEVICE NAME INTO A SUGGESTED IC3 FNAME
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import re
import unicodedata

# Characters Apple (or the keyboard) may use in a device name and what they are
# changed to so the name can be parsed: Curly/modifier apostrophes and no-break space
NAME_CHAR_REPLACEMENTS = {
    "\u2019": "'",      # ’ right single quotation mark (Apple's default "Gary’s iPhone")
    "\u2018": "'",      # ‘ left single quotation mark
    "\u02bc": "'",      # ʼ modifier letter apostrophe
    "\u00a0": " ",      # no-break space
}

# ---------------------------------------------------------------------------
# device_type is passed in pre-resolved as one of these exact keywords.
# Output renames only "Apple Watch" → "Watch" ("Watch" passed in maps to itself).
# ---------------------------------------------------------------------------
DEVICE_TYPE_OUTPUT = {
    "iPhone":      "iPhone",
    "iPad":        "iPad",
    "Apple Watch": "Watch",
    "Watch":       "Watch",
    "Mac":         "Mac",
    "AirPods":     "AirPods",
}

# ---------------------------------------------------------------------------
# Prepositions / particles — device-first languages
# e.g. "iPhone de Philippe",  "iPad van Jan"
# ---------------------------------------------------------------------------
DEVICE_FIRST_PARTICLES = [
    "d'en ", "d'", "de ", "do ", "da ",   # French / Spanish / Portuguese / Catalan
    "di ",                                  # Italian
    "van ",                                 # Dutch
    "til ",                                 # Norwegian/Danish
    "lui ",                                 # Romanian
    "של ",                                  # Hebrew
    "لـ", "ل",                             # Arabic
    "ของ ",                                 # Thai
    "của ",                                 # Vietnamese
    "του ", "της ",                         # Greek
    "का ", "की ", "के ",                   # Hindi
]

# Possessive suffixes appended to the NAME in name-first languages
NAME_SUFFIX_PARTICLES = [
    "'nin", "'nın", "'nün", "'nün",         # Turkish
    "'un",  "'ün",  "'in",  "'ın",
]

# Regex to discard a model suffix that follows the device keyword WITHIN
# raw_name itself (e.g. raw_name="Gary's iPad Pro" even though
# device_type="iPad"). This only ever operates on raw_name, never device_type.
_SUFFIX_RE = re.compile(
    r"""^
        (?:
            [\s\-]+
            (?:
                \d[\d\s]*           # digit(s): 15, 16, M2
              | [A-Z][a-z]+         # CamelCase word: Pro, Air, Ultra, Mini …
              | [A-Z]{2,}           # acronym: SE
            )
        )+
    """,
    re.VERBOSE,
)

#----------------------------------------------------------------------------
def name_device_type_key(raw_name, device_type, first_name=None):
    '''
    Return the name used to recognize a replacement device of the same person,
    e.g. "lillian-watch" for "Lillian-Watch", "Lillian Watch" and "Lillian's Apple Watch".
    A device name that can not be parsed is returned lower case with spaces and
    underscores changed to a '-', the same as slugify treats them.
    '''
    name = make_ic3_fname_from_aadevice_dname(raw_name, device_type, first_name)
    return re.sub(r"[\s\-_]+", "-", name.strip()).lower()

#----------------------------------------------------------------------------
def make_ic3_fname_from_aadevice_dname(raw_name, device_type, first_name=None):
    """
    Parse an Apple-style localised device name and return "Name-DeviceType".

    Parameters
    ----------
    raw_name : str
        The full localized device name, e.g. "Gary's iPhone",
        "iPhone de Philippe", "Garyn iPhone", "Gary iPhone-ja".
    device_type : str
        Exact keyword already resolved by the caller — one of:
        "iPhone", "iPad", "Apple Watch", "Watch", "Mac", "AirPods".
        No model info is present in this value. "Watch" (the Apple deviceClass)
        also finds "Apple Watch" in raw_name.
    first_name : str
        The device owner's first name from Apple (userInfo or membersInfo). If
        the name part of raw_name is the first name, it is not shortened by the
        Finnish '-n' or Germanic '-s' possessive rules ("Lillian iPhone" is
        "Lillian", not "Lillia").

    Returns
    -------
    str
        "Name-DeviceType" on success.
        The original raw_name, unchanged, if device_type isn't a recognized
        keyword, the keyword isn't found in raw_name, raw_name does not have a
        possessive ("KenniPad 11", "iPhone Gary", "Lillian-Watch") or no name
        could be extracted.
    """

    output_name = DEVICE_TYPE_OUTPUT.get(device_type)
    if output_name is None:
        return raw_name  # not a recognized/tracked device type

    raw = _normalise(raw_name)
    has_possessive = False

    # Apple's default watch name is "Gary's Apple Watch" but the deviceClass is "Watch"
    if device_type == "Watch" and "Apple Watch" in raw:
        device_type = "Apple Watch"

    # Romanian: "iPhone-ul" → "iPhone"
    if f"{device_type}-ul" in raw:
        raw = raw.replace(f"{device_type}-ul", device_type, 1)
        has_possessive = True

    # Turkish device-word suffix: "iPhone'u" → "iPhone"
    for sfx in ("'u", "'ü", "'ı", "'i", "\u2019u", "\u2019ü", "\u2019ı", "\u2019i"):
        if f"{device_type}{sfx}" in raw:
            raw = raw.replace(f"{device_type}{sfx}", device_type, 1)
            has_possessive = True
            break

    # Chinese 的 / Hindi possession markers
    for particle in ("的", "का", "की", "के"):
        if particle in raw:
            raw = raw.replace(particle, " ").strip()
            has_possessive = True

    found = _find_device_in_raw(raw, device_type)
    if found is None:
        return raw_name  # keyword wasn't actually present in raw_name

    remainder, device_was_first = found

    # Hungarian check on original (pre-cleaning) raw string
    hungarian_name = _try_hungarian(_normalise(raw_name), device_type)
    if hungarian_name:
        return f"{hungarian_name}-{output_name}"

    name, particle_found = (_strip_device_first_particles(remainder)
                            if device_was_first
                            else _strip_name_first_particles(remainder, first_name))

    if has_possessive is False and particle_found is False:
        return raw_name  # no possessive, the name is not an Apple default name

    name = name.strip(" -–—'\u2019")
    return f"{name}-{output_name}" if name else raw_name


# ---------------------------------------------------------------------------
def _normalise(text: str) -> str:
    '''
    Change curly apostrophes and no-break spaces so the name can be parsed even
    if the caller did not already change them
    '''
    for from_char, to_char in NAME_CHAR_REPLACEMENTS.items():
        text = text.replace(from_char, to_char)
    return unicodedata.normalize("NFC", text.strip())

# ---------------------------------------------------------------------------
def _strip_model_suffix(after: str) -> str:
    """Discard any model/generation suffix following the keyword in raw_name."""
    m = _SUFFIX_RE.match(after)
    return after[m.end():] if m else after

# ---------------------------------------------------------------------------
def _find_device_in_raw(raw: str, keyword: str):
    """
    Locate *keyword* inside *raw* (the full localized device name string)
    and return (remainder, device_was_first), or None if not found.
    The remainder before the keyword is not stripped so the Finnish -n and
    Germanic -s rules can tell "Garys iPhone" from "KensiPhone".
    """
    idx = raw.find(keyword)
    if idx == -1:
        return None

    before = raw[:idx]
    after  = _strip_model_suffix(raw[idx + len(keyword):])

    return (after.strip(), True) if idx == 0 else (before, False)

# ---------------------------------------------------------------------------
def _strip_device_first_particles(remainder: str) -> tuple[str, bool]:
    """
    Remove preposition between device and name: 'de Philippe' → 'Philippe'.
    Return (name, particle_found).
    """
    for p in DEVICE_FIRST_PARTICLES:
        if remainder.startswith(p):
            return remainder[len(p):].strip(), True
    return remainder.strip(), False

# ---------------------------------------------------------------------------
def _strip_name_first_particles(remainder: str, first_name=None) -> tuple[str, bool]:
    """
    Remove possessive marker after name: 'Gary's' → 'Gary'.
    Return (name, particle_found).
    """
    # The Finnish -n and Germanic -s are only a possessive if the name is
    # separated from the device ("Garys iPhone", not "KensiPhone")
    separated = remainder[-1:].isspace()
    s = remainder.strip()

    # The name is the owner's first name, there is no possessive to remove
    # ('Lillian' would be changed to 'Lillia' by the Finnish -n rule)
    name = s.strip(" -–—")
    if first_name and name.lower() == first_name.strip().lower():
        return name, False

    for ch in ("の", "의"):                # Japanese / Korean
        if s.endswith(ch):
            return s[:-1].strip(), True

    for apos in ("'s", "\u2019s"):         # English
        if s.endswith(apos):
            return s[:-2].strip(), True

    for sfx in NAME_SUFFIX_PARTICLES:      # Turkish
        if sfx in s:
            return s[:s.rfind(sfx)].strip(), True

    if separated and s.endswith("n") and len(s) > 2 and s[-2] != "n":    # Finnish -n
        return s[:-1].strip(), True

    if separated and s.endswith("s") and len(s) > 1 and s[-2].isalpha(): # Germanic bare -s
        return s[:-1].strip(), True

    return s, False

# ---------------------------------------------------------------------------
def _try_hungarian(raw: str, keyword: str) -> str | None:
    """Hungarian appends suffix to device word: 'Gary iPhone-ja' → 'Gary'."""
    for sfx in ("-ja", "-je", "-a", "-e"):
        candidate = keyword + sfx
        if candidate in raw:
            before = raw[:raw.find(candidate)].strip()
            if before:
                return before
    return None



# ---------------------------------------------------------------------------
# Self-test: python device_name_parser.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        # (raw_name, device_type, expected, first_name)
        # ── iPhone ───────────────────────────────────────────────────────────
        ("Gary's iPhone",                  "iPhone", "Gary-iPhone", None),
        ("Gary\u2019s iPhone",             "iPhone", "Gary-iPhone", None),
        ("iPhone de Philippe",             "iPhone", "Philippe-iPhone", None),
        ("iPhone de María",                "iPhone", "María-iPhone", None),
        ("iPhone de João",                 "iPhone", "João-iPhone", None),
        ("iPhone di Marco",                "iPhone", "Marco-iPhone", None),
        ("iPhone van Jan",                 "iPhone", "Jan-iPhone", None),
        ("Garys iPhone",                   "iPhone", "Gary-iPhone", None),
        ("Garyn iPhone",                   "iPhone", "Gary-iPhone", None),
        ("iPhone Гарри",                   "iPhone", "iPhone Гарри", None),
        ("iPhone Jana",                    "iPhone", "iPhone Jana", None),
        ("Gary iPhone-ja",                 "iPhone", "Gary-iPhone", None),
        ("iPhone-ul lui Gary",             "iPhone", "Gary-iPhone", None),
        ("Gary'nin iPhone'u",              "iPhone", "Gary-iPhone", None),
        ("Gary\u2019nin iPhone\u2019u",    "iPhone", "Gary-iPhone", None),
        ("Gary\u306eiPhone",               "iPhone", "Gary-iPhone", None),
        ("Gary\u7684iPhone",               "iPhone", "Gary-iPhone", None),
        ("Gary\uc758 iPhone",              "iPhone", "Gary-iPhone", None),
        ("iPhone \u0644\u0640 Gary",       "iPhone", "Gary-iPhone", None),
        ("iPhone \u05e9\u05dc Gary",       "iPhone", "Gary-iPhone", None),
        ("iPhone \u0e02\u0e2d\u0e07 Gary", "iPhone", "Gary-iPhone", None),
        ("iPhone c\u1ee7a Gary",           "iPhone", "Gary-iPhone", None),
        ("iPhone Gary",                    "iPhone", "iPhone Gary", None),
        ("iPhone d'en Gary",               "iPhone", "Gary-iPhone", None),
        # ── No possessive → original raw_name returned ───────────────────────
        ("Lillian iPhone",                 "iPhone", "Lillian iPhone", "Lillian"),
        ("Lillian\u00a0iPhone",            "iPhone", "Lillian\u00a0iPhone", "Lillian"),
        ("Chris iPhone",                   "iPhone", "Chris iPhone", "Chris"),
        ("Lillian-iPhone",                 "iPhone", "Lillian-iPhone", "Lillian"),
        ("Garyn iPhone",                   "iPhone", "Gary-iPhone", "Gary"),
        ("CathiPad 11",                    "iPad",   "CathiPad 11", None),
        ("CathiPhone",                     "iPhone", "CathiPhone", None),
        ("KenniPad 13",                    "iPad",   "KenniPad 13", None),
        ("KenniPhone",                     "iPhone", "KenniPhone", None),
        ("KenniWatch7",                    "Watch",  "KenniWatch7", None),
        ("KensiPhone",                     "iPhone", "KensiPhone", None),
        # ── iPad (raw_name may include model, device_type never does) ────────
        ("Gary\u2019s iPad",               "iPad", "Gary-iPad", None),
        ("Gary\u2019s iPad Air",           "iPad", "Gary-iPad", None),
        ("Gary\u2019s iPad Air M2",        "iPad", "Gary-iPad", None),
        ("Gary\u2019s iPad Pro",           "iPad", "Gary-iPad", None),
        ("Gary\u2019s iPad mini",          "iPad", "Gary-iPad", None),
        ("iPad de Sophie",                 "iPad", "Sophie-iPad", None),
        # ── Watch ────────────────────────────────────────────────────────────
        ("Gary\u2019s Apple Watch",         "Apple Watch", "Gary-Watch", None),
        ("Gary\u2019s Apple Watch SE",      "Apple Watch", "Gary-Watch", None),
        ("Gary\u2019s Apple Watch Ultra 2", "Apple Watch", "Gary-Watch", None),
        ("Apple Watch de Pierre",           "Apple Watch", "Pierre-Watch", None),
        ("Gary\u2019s Watch",               "Watch",       "Gary-Watch", None),
        # deviceClass "Watch" with Apple's default name
        ("Lillian\u2019s Apple Watch",      "Watch",       "Lillian-Watch", "Lillian"),
        ("Lillian's Apple Watch",           "Watch",       "Lillian-Watch", None),
        ("Lillian-Watch",                   "Watch",       "Lillian-Watch", "Lillian"),
        ("Apple Watch de Pierre",           "Watch",       "Pierre-Watch", None),
        # ── Mac ──────────────────────────────────────────────────────────────
        ("Gary\u2019s Mac",                "Mac", "Gary-Mac", None),
        ("Gary\u2019s MacBook Pro",        "Mac", "Gary-Mac", None),
        ("Gary\u2019s Mac mini",           "Mac", "Gary-Mac", None),
        ("Garys Mac",                      "Mac", "Gary-Mac", None),
        # ── AirPods ──────────────────────────────────────────────────────────
        ("Gary\u2019s AirPods",            "AirPods", "Gary-AirPods", None),
        ("Gary\u2019s AirPods Pro",        "AirPods", "Gary-AirPods", None),
        ("AirPods de Sophie",              "AirPods", "Sophie-AirPods", None),
        # ── Unrecognized device_type → original raw_name returned ───────────
        ("Gary\u2019s HomePod mini",       "HomePod", "Gary\u2019s HomePod mini", None),
        # ── Keyword not actually present in raw_name → original returned ────
        ("Some weird unparseable string",  "iPhone",  "Some weird unparseable string", None),
    ]

    print(f"{'raw_name':<32} {'device_type':<14} {'Expected':<28} {'Got':<28} OK?")
    print("-" * 110)
    all_pass = True
    for raw, dtype, expected, first_name in tests:
        got = make_ic3_fname_from_aadevice_dname(raw, dtype, first_name)
        ok  = "✓" if got == expected else "✗"
        if got != expected:
            all_pass = False
        print(f"{raw:<32} {dtype:<14} {expected:<28} {got:<28} {ok}")
    print()
    print("All tests passed!" if all_pass else "Some tests FAILED.")
