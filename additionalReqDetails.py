charIDs = {
    0: 'Paul',
    1: 'Law',
    2: 'King',
    3: 'Yoshimitsu',
    4: 'Hwoarang',
    5: 'Xiayou',
    6: 'Jin',
    7: 'Bryan',
    8: 'Kazuya',
    9: 'Steve',
    10: 'Jack-8',
    11: 'Asuka',
    12: 'Devil Jin',
    13: 'Feng',
    14: 'Lili',
    15: 'Dragunov',
    16: 'Leo',
    17: 'Lars',
    18: 'Alisa',
    19: 'Claudio',
    20: 'Shaheen',
    21: 'Nina',
    22: 'Lee',
    23: 'Kuma',
    24: 'Panda',
    25: 'Zafina',
    26: 'Leroy',
    27: 'Jun',
    28: 'Reina',
    29: 'Azucena',
    30: 'Raven',
    31: 'Victor',
    32: 'Azazel',
    33: 'Eddy',
    34: 'Lidia',
    35: 'Heihachi',
    36: 'Clive',
    37: 'Anna',
    38: 'Fahkumram',
    39: 'Armor King',
    40: 'Miary Zo',
    116: 'Dummy',
    117: 'Angel Jin',
    118: 'True Devil Kazuya',
    119: 'Jack-7',
    120: 'Soldier',
    121: 'Devil Jin (v2)',
    122: 'Tekken Monk',
    123: 'Seiryu',
}

gamemodes = {
    0: "Arcade Mode",
    1: "Practice",
    4: "Main Story",
    5: "Char episode",
    6: "Customization",
    10: "VS"
}

reqYesNo = {
    0: "No",
    1: "Yes"
}

req225 = {
    0: "Player",
    1: "CPU",
    3: "Intro/Outro?"
}

req567 = {
    3: "Story prefight",
    4: "Story postfight?",
    # 8: "Treasure Battle, post-fight???",
    # 10: "Arcade??",
    12: "Story postfight?",
    17: "Continue? timer",
    18: "Customization: Stand",
    33: "Customization sequence play?",
}


checkInput = {
    0x1: "1",
    0x2: "2",
    0x3: "1+2",
    0x4: "3",
    0x5: "1+3",
    0x6: "2+3",
    0x7: "1+2+3",
    0x8: "4",
    0x9: "1+4",
    0xA: "2+4",
    0xB: "1+2+4",
    0xC: "3+4",
    0xD: "1+3+4",
    0xE: "2+3+4",
    0xF: "1+2+3+4",
}


# Helper functions
def lookup(data_dict):
    """Returns a function that looks up the value in the provided dictionary."""
    def _lookup(x, default):
        return data_dict.get(x, default)
    return _lookup


def flag_check(operator):
    """Returns a function that formats a flag comparison."""
    def _check(x, default):
        try:
            val = int(x)
        except (ValueError, TypeError):
            return default
        flag = val >> 16
        value = val & 0xFFFF
        return f"flag {flag} {operator} {value}"
    return _check


def story_battle_req(x, default):
    """Formats story battle requirement."""
    try:
        battle_code = int(x)
        chapter = (battle_code & 0xF0) >> 4
        fight = battle_code & 0xF
        return f"CH {chapter} BT {fight}"
    except (ValueError, TypeError):
        return default


# Formatting: reqId -> processor_function
reqDetailsList = {
    159: lookup(reqYesNo),
    220: lookup(charIDs),
    221: lookup(charIDs),
    222: lookup(charIDs),
    223: lookup(charIDs),
    224: lookup(charIDs),
    225: lookup(charIDs),
    226: lookup(charIDs),
    227: lookup(charIDs),
    228: lookup(req225),  # Player is CPU
    229: lookup(req225),  # Player is CPU
    288: flag_check(">="),
    326: flag_check("<="),
    365: flag_check("=="),
    453: lookup(checkInput),  # Check Input
    454: lookup(reqYesNo),  # Bryan Snake Eyes
    473: lookup(reqYesNo),  # Perma devil
    498: lookup(reqYesNo),  # Heihachi Warrior Instinct
    668: story_battle_req,
    672: lookup(gamemodes),
    1028: lookup(reqYesNo),
}
