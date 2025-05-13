from Addresses import AddressFile, GameClass


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
