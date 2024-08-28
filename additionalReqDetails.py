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
    36: 'DLC4',
    116: 'Dummy',
    117: 'Angel Jin',
    118: 'True Devil Kazuya',
    119: 'Jack-7',
    120: 'Soldier',
    121: 'Devil Jin (v2)'
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

def getStoryBattle(battleCode: int):
    chapter = (battleCode & 0xF0) >> 4
    fight = battleCode & 0xF
    return "CH %d BT %d" % (chapter, fight)


class Requirement:
    def get(self, x, default):
        raise NotImplementedError(
            "This method should be overridden by subclasses")


class DictionaryRequirement(Requirement):
    def __init__(self, data):
        self.data = data

    def get(self, x, default):
        return self.data.get(x, default)


class ShortFlagGT(Requirement):
    def get(self, x, default):
        try:
            y = int(x)
        except:
            return default
        flag = x >> 16
        value = x & 0xFFFF
        return f"flag {flag} >= {value}"


class ShortFlagLT(Requirement):
    def get(self, x, default):
        try:
            y = int(x)
        except:
            return default
        flag = x >> 16
        value = x & 0xFFFF
        return f"flag {flag} <= {value}"


class ShortFlagEQ(Requirement):
    def get(self, x, default):
        try:
            y = int(x)
        except:
            return default
        flag = x >> 16
        value = x & 0xFFFF
        return f"flag {flag} == {value}"


class StoryBattleRequirement(Requirement):
    def get(self, x, default):
        try:
            battle_code = int(x)
            return getStoryBattle(battle_code)
        except:
            return default


# Function to get story battle details
def getStoryBattle(battleCode: int):
    chapter = (battleCode & 0xF0) >> 4
    fight = battleCode & 0xF
    return f"CH {chapter} BT {fight}"


# Add req in this list and assign parameter list
# Format: reqId -> paramList
reqDetailsList = {
    159: DictionaryRequirement(reqYesNo),
    220: DictionaryRequirement(charIDs),  # Char ID checks
    221: DictionaryRequirement(charIDs),
    222: DictionaryRequirement(charIDs),
    223: DictionaryRequirement(charIDs),
    224: DictionaryRequirement(charIDs),
    225: DictionaryRequirement(charIDs),
    226: DictionaryRequirement(charIDs),
    227: DictionaryRequirement(charIDs),
    228: DictionaryRequirement(req225),  # Player is CPU
    229: DictionaryRequirement(req225),  # Player is CPU
    288: ShortFlagGT(),  # Short flag >= X
    326: ShortFlagLT(),  # Short flag <= X
    365: ShortFlagEQ(),  # Short flag == X
    454: DictionaryRequirement(reqYesNo), # Bryan Snake Eyes
    668: StoryBattleRequirement(),  # Story battle details
    672: DictionaryRequirement(gamemodes),  # Game mode
    1028: DictionaryRequirement(reqYesNo),
}
