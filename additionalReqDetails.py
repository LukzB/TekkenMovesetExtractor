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
    30: 'Raven', # Placement of ID not 100% confirmed, just intuition
    31: 'Victor', # Placement of ID not 100% confirmed, just intuition
    32: 'Dummy',
    33: 'DLC1',
    34: 'DLC2',
    35: 'DLC3',
    36: 'DLC4',
    116: '???',
    117: '???',
    118: '???',
    119: 'Jack-7',
    120: '???',
    121: '???'
}

gamemodes = {
    0: "Arcade Mode",
    1: "Practice",
    4: "Main Story",
    5: "Char episode",
    6: "Customization",
    7: "Treasure Battle",
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

storyBattles = {
    0: "Prologue",
    1: "Throwing KAZ off cliff",
    2: "HEI vs T-Force",
    3: "HEI vs NINA",
    4: "KAZ vs JACK4",
    5: "HEI vs JACK4",
    6: "HEI vs CLAUDIO",
    7: "LARS vs G-CORP",
    9: "LEE vs ALISA",
    10: "ALISA vs T-FORCE",
    11: "LEEs vs T-FORCE",
    12: "HEI vs AKUMA 1",
    13: "HEI vs JACK6",
    14: "HEI vs AKUMA 2",
    15: "ALISA vs NINA 1",
    16: "ALISA vs NINA 2",
    18: "KAZ vs AKUMA 1",
    19: "KAZ vs AKUMA 2",
    21: "HEI vs KAZUMI",
    22: "HEI vs KAZ 1",
    23: "HEI vs KAZ 2",
    24: "HEI vs KAZ 3",
    25: "HEI vs KAZ 4",
    26: "???",
    27: "Special Chapter"
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


class req284:
    def get(self, x, default):
        try:
            y = int(x)
        except:
            return default
        flag = x >> 16
        value = x & 0xFFFF
        output = "Player flag %d >= %d" % (flag, value)
        return output


class req359:
    def get(self, x, default):
        try:
            y = int(x)
        except:
            return default
        flag = x >> 16
        value = x & 0xFFFF
        output = "Player flag %d == %d" % (flag, value)
        return output


# Add req in this list and assign parameter list
# Format: reqId -> paramList
reqDetailsList = {
    158: reqYesNo,
    159: reqYesNo,
    220: charIDs,  # Char ID checks
    221: charIDs,
    222: charIDs,
    223: charIDs,
    224: charIDs,
    225: charIDs,
    226: charIDs,
    227: charIDs,
    228: req225,  # Player is CPU
    287: req284(),  # Player flag >= X
    362: req359(),  # Player flag == X
    # 562: storyBattles,  # Story Battle Number
    566: gamemodes,  # Game mode
}
