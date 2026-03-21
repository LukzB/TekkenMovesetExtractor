from Addresses import AddressFile, GameClass

CHAR_CODE_MAPPING = {
    0: 'grf',
    1: 'pig',
    2: 'pgn',
    3: 'cml',
    4: 'snk',
    5: 'rat',
    6: 'ant',
    7: 'cht',
    8: 'grl',
    9: 'bsn',
    10: 'ccn',
    11: 'der',
    12: 'swl',
    13: 'klw',
    14: 'hms',
    15: 'kmd',
    16: 'ghp',
    17: 'lzd',
    18: 'mnt',
    19: 'ctr',
    20: 'hrs',
    21: 'kal',
    22: 'wlf',
    23: 'rbt',
    24: 'ttr',
    25: 'crw',
    26: 'jly',
    27: 'aml',
    28: 'zbr',
    29: 'cat',
    30: 'lon',
    31: 'bbn',
    32: 'got',
    33: 'dog',
    34: 'cbr',
    35: 'bee',
    36: 'okm',
    37: 'kgr',
    38: 'tgr',
    39: 'knk',
    40: 'wkz',
    117: 'xxa',
    118: 'xxb',
    119: 'xxc',
    120: 'xxd',
    121: 'xxe',
    122: 'xxf',
    123: 'xxg',
    128: 'test'
}

def getCharacterCode(charId):
    return CHAR_CODE_MAPPING.get(charId, 'Unknown')


def getPlayerPointerPath(playerId):
    # return [0x10, 0xB0, 0x58 - playerId * 8, 0] # For customization
    # return [0x10, 0xB0, 0x50 + playerId * 8, 0] # For customization
    return [0x30 + playerId * 8, 0]


def aobScan(game: GameClass, pattern, start_addr, end_addr):
    try:
        return game.aobScan(pattern, start_addr, end_addr, False)
    except:
        return None


def scanPlayerBaseAddress(game: GameClass):
    base = game.moduleAddr
    addr = aobScan(
        game=game,
        pattern="4C 89 35 ?? ?? ?? ?? 41 88 5E 28 66 41 89 9E 88 00 00 00 E8 ?? ?? ?? ?? 41 88 86 8A 00 00 00",
        start_addr=base + 0x5A00000,
        end_addr=base + 0x6F00000,
    )
    return (addr + 7 + game.readInt(addr + 3) - base) if addr else None


def scanMovesetOffset(game: GameClass):
    base = game.moduleAddr
    addr = aobScan(
        game=game,
        pattern="48 89 91 ?? ?? ?? 00 4C 8B D9 48 89 91 ?? ?? ?? 00 48 8B DA 48 89 91 ?? ?? ?? 00 48 89 91 ?? ?? ?? 00 0F B7 02 89 81 ?? ?? ?? 00 B8 01 80 00 80",
        start_addr=base + 0x1800000,
        end_addr=base + 0x2800000,
    )
    return game.readInt(addr + 3) if addr else None


def scanGameAddresses(game: GameClass, game_addresses: AddressFile):
    is_empty = lambda key: game_addresses[key] is None or game_addresses[key] == 0

    if (is_empty("t8_p1_addr") and is_empty("t8_motbin_offset")):
        print("Scanning addresses")

    key = "t8_p1_addr"
    if is_empty(key):
        addr = scanPlayerBaseAddress(game)
        if addr:
            game_addresses.setAddress(key, addr, True)

    key = "t8_motbin_offset"
    if is_empty(key):
        addr = scanMovesetOffset(game)
        if addr:
            game_addresses.setAddress(key, addr)
    return
