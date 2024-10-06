# --- Ton-Chan's Motbin import --- #
# Python 3.6.5

from Addresses import game_addresses, GameClass, VirtualAllocEx, VirtualFreeEx, GetLastError, MEM_RESERVE, MEM_COMMIT, MEM_DECOMMIT, MEM_RELEASE, PAGE_EXECUTE_READWRITE
from Aliases import getTekken8characterName, getRequirementAlias, getMoveExtrapropAlias, getCharacteridAlias, ApplyCharacterFixes, fillAliasesDictonnaries, getHitboxAliases, applyGlobalRequirementAliases
import json
import os
import sys
from copy import deepcopy

importVersion = "1.0.1"

requirement_size = 0x14
cancel_size = 0x28
cancel_extradata_size = 0x4
move_size = 0x3A0
reaction_list_size = 0x70
hit_condition_size = 0x18
pushback_size = 0x10
pushback_extra_size = 0x2
extra_move_property_size = 0x28
other_move_props_size = 0x20
voiceclip_size = 0xC
input_sequence_size = 0x10
input_extradata_size = 0x8
projectile_size = 0xD8
throw_extras_size = 0xC
throws_size = 0x10
parry_related_size = 0x4
dialogues_size = 0x18

placeholder_address = 0x146FD2500

forbiddenMoves = ['Co_DA_Ground']


def readJsonFile(folderName: str):
    jsonFilename = next(file for file in os.listdir(
        folderName) if file.endswith(".json"))
    print("Reading %s..." % (jsonFilename))
    with open("%s/%s" % (folderName, jsonFilename), "r") as f:
        m = json.load(f)
        f.close()
        return m

def printPtrInfo(p):
    print("%d/%d bytes left." % (p.size - (p.curr_ptr - p.head_ptr), p.size))
    return

class Importer:
    def __init__(self, gameName="Polaris-Win64-Shipping.exe"):
        self.T = GameClass(gameName)
        self.T.applyModuleAddress(game_addresses)

    def readInt(self, addr, bytes_length=4):
        return self.T.readInt(addr, bytes_length)

    def writeInt(self, addr, value, bytes_length=0):
        return self.T.writeInt(addr, value, bytes_length=bytes_length)

    def readBytes(self, addr, bytes_length):
        return self.T.readBytes(addr, bytes_length)

    def writeBytes(self, addr, data):
        return self.T.writeBytes(addr, data)

    def writeString(self, addr, text):
        return self.writeBytes(addr, bytes(text + "\x00", 'ascii'))

    def readString(self, addr):
        offset = 0
        while self.readInt(addr + offset, 1) != 0:
            offset += 1
        return self.readBytes(addr, offset).decode("ascii")

    def allocateMem(self, allocSize):
        return VirtualAllocEx(self.T.handle, 0, allocSize, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)

    def getPlayerAddress(self, playerid):
        playerAddr = game_addresses['t8_p1_addr']

        if playerAddr == 0:
            return None

        if playerid == 1:
            playerAddr += game_addresses['t8_playerstruct_size']

        return playerAddr

    def importMoveset(self, playerAddr, folderName, moveset=None, charactersPath='extracted_chars/'):
        if moveset == None:
            moveset = readJsonFile(folderName)

        loaded_chara_id = self.readInt(
            playerAddr + game_addresses['t8_chara_id_offset'])

        if loaded_chara_id != moveset['character_id']:
            print("Cannot import because a different character is loaded")
            return None

        motbin_ptr_addr = playerAddr + game_addresses['t8_motbin_offset']
        current_motbin_ptr = self.readInt(motbin_ptr_addr, 8)
        global placeholder_address
        placeholder_address = self.readInt(current_motbin_ptr + 0x10, 8)

        moveset = self.loadMoveset(
            folderName=folderName, moveset=moveset, charactersPath=charactersPath)

        try:
            old_character_name = getTekken8characterName(moveset.m['character_id'])
            old_character_name = old_character_name[1:-1]
        except:
            old_character_name = "???"

        # moveset.copyMotaOffsets(current_motbin_ptr)
        # moveset.applyCharacterIDAliases(playerAddr)

        print("\nOLD moveset pointer: 0x%x (%s)" %
              (current_motbin_ptr, old_character_name))
        print("NEW moveset pointer: 0x%x (%s)" %
              (moveset.motbin_ptr, moveset.m['character_name']))

        self.writeInt(motbin_ptr_addr, moveset.motbin_ptr, 8)

        moveset.updateCameraMotaStaticPointer(playerAddr)

        return moveset

    def loadMoveset(self, folderName=None, moveset=None, charactersPath=None):
        if moveset == None:
            m = readJsonFile(folderName)
        else:
            m = deepcopy(moveset)

        if 'export_version' not in m or not versionMatches(m['export_version']):
            print("Error: trying to import outdated moveset, please extract again.")
            raise Exception("Moveset version: %s. Importer version: %s." % (
                m['export_version'], importVersion))

        fillAliasesDictonnaries(m['version'])

        # ApplyCharacterFixes(m)

        p = MotbinStruct(m, folderName, self, animSearchFolder=charactersPath)

        # character_name = p.writeString(m['character_name'])
        # creator_name = p.writeString("creator")
        # date = p.writeString("date")
        # fulldate = p.writeString("date_full")

        requirements_ptr, requirement_count = p.allocateRequirements()
        cancel_extradata_ptr, cancel_extradata_size = p.allocateCancelExtradata()
        cancel_ptr, cancel_count = p.allocateCancels(m['cancels'])
        group_cancel_ptr, group_cancel_count = p.allocateCancels(m['group_cancels'], grouped=True)
        pushback_extras_ptr, pushback_extras_count = p.allocatePushbackExtras()
        pushback_ptr, pushback_list_count = p.allocatePushbacks()
        reaction_list_ptr, reaction_list_count = p.allocateReactionList()
        extra_move_properties_ptr, extra_move_properties_count = p.allocateExtraMoveProperties()
        move_start_props_ptr, move_start_props_count = p.allocateMoveStartProperties()
        move_end_props_ptr, move_end_props_count = p.allocateMoveEndProperties()
        voiceclip_list_ptr, voiceclip_list_count = p.allocateVoiceclipIds()
        hit_conditions_ptr, hit_conditions_count = p.allocateHitConditions()
        moves_ptr, move_count = p.allocateMoves()
        input_extradata_ptr, input_extradata_count = p.allocateInputExtradata()
        input_sequences_ptr, input_sequences_count = p.allocateInputSequences()
        projectiles_ptr, projectiles_count = p.allocateProjectiles()
        throw_extras_ptr, throw_extras_count = p.allocateThrowExtras()
        throws_ptr, throws_count = p.allocateThrows()
        parry_related_ptr, parry_related_count = p.allocateParryRelated()
        dialogues_ptr, dialogues_count = p.allocateDialogueHandlers()

        p.allocateMota()

        self.writeInt(p.motbin_ptr + 0x0, 65536, 4)
        self.writeInt(p.motbin_ptr + 0x4, m['_0x4'], 4)
        self.writeInt(p.motbin_ptr + 0x8, 0x4B4554, 4)

        # self.writeInt(p.motbin_ptr, character_name, 8)
        # self.writeInt(p.motbin_ptr, creator_name, 8)
        # self.writeInt(p.motbin_ptr, date, 8)
        # self.writeInt(p.motbin_ptr, fulldate, 8)

        self.writeInt(p.motbin_ptr + 0x10, placeholder_address, 8)
        self.writeInt(p.motbin_ptr + 0x18, placeholder_address, 8)
        self.writeInt(p.motbin_ptr + 0x20, placeholder_address, 8)
        self.writeInt(p.motbin_ptr + 0x28, placeholder_address, 8)

        self.writeAliases(p.motbin_ptr, m)

        self.writeInt(p.motbin_ptr + 0x168, reaction_list_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x178, reaction_list_count, 8)

        self.writeInt(p.motbin_ptr + 0x180, requirements_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x188, requirement_count, 8)

        self.writeInt(p.motbin_ptr + 0x190, hit_conditions_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x198, hit_conditions_count, 8)

        self.writeInt(p.motbin_ptr + 0x1A0, projectiles_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x1A8, projectiles_count, 8)

        self.writeInt(p.motbin_ptr + 0x1B0, pushback_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x1B8, pushback_list_count, 8)

        self.writeInt(p.motbin_ptr + 0x1C0, pushback_extras_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x1C8, pushback_extras_count, 8)

        self.writeInt(p.motbin_ptr + 0x1D0, cancel_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x1D8, cancel_count, 8)

        self.writeInt(p.motbin_ptr + 0x1E0, group_cancel_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x1E8, group_cancel_count, 8)

        self.writeInt(p.motbin_ptr + 0x1F0, cancel_extradata_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x1F8, cancel_extradata_size, 8)

        self.writeInt(p.motbin_ptr + 0x200, extra_move_properties_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x208, extra_move_properties_count, 8)

        self.writeInt(p.motbin_ptr + 0x210, move_start_props_ptr, 8)  # ??
        self.writeInt(p.motbin_ptr + 0x218, move_start_props_count, 8)  # ??

        self.writeInt(p.motbin_ptr + 0x220, move_end_props_ptr, 8)  # ??
        self.writeInt(p.motbin_ptr + 0x228, move_end_props_count, 8)  # ??

        self.writeInt(p.motbin_ptr + 0x230, moves_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x238, move_count, 8)

        self.writeInt(p.motbin_ptr + 0x240, voiceclip_list_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x248, voiceclip_list_count, 8)

        self.writeInt(p.motbin_ptr + 0x250, input_sequences_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x258, input_sequences_count, 8)

        self.writeInt(p.motbin_ptr + 0x260, input_extradata_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x268, input_extradata_count, 8)

        self.writeInt(p.motbin_ptr + 0x270, parry_related_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x278, parry_related_count, 8)

        self.writeInt(p.motbin_ptr + 0x280, throw_extras_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x288, throw_extras_count, 8)

        self.writeInt(p.motbin_ptr + 0x290, throws_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x298, throws_count, 8)

        self.writeInt(p.motbin_ptr + 0x2A0, dialogues_ptr, 8)
        self.writeInt(p.motbin_ptr + 0x2A8, dialogues_count, 8)

        # p.applyMotaOffsets()

        print("%s (ID: %d) successfully imported in memory at 0x%x." %
              (m['character_name'], m['character_id'], p.motbin_ptr))
        # print this to check if any allocated byte has not been used (written on)
        printPtrInfo(p)

        return p

    def writeAliases(self, motbin_ptr, m):
        alias_offset = 0x30  # was 0x28

        if m["version"] == "Tekken5" or m["version"] == "Tekken5DR":  # different alias system for T5
            for i in range(2):
                for i in range(36):
                    self.writeInt(motbin_ptr + alias_offset,
                                  m['aliases'][i], 2)
                    alias_offset += 2
                for i in range(20):
                    self.writeInt(motbin_ptr + alias_offset, 0, 2)
                    alias_offset += 2
        elif m["version"] == "Tekken8":
            print("Moveset belongs to Tekken 8, writing corresponding aliases...")
            for alias in m['original_aliases']:
                self.writeInt(motbin_ptr + alias_offset, alias, 2)
                alias_offset += 2
            if 'current_aliases' in m:
                alias_offset = 0xA8
                for alias in m['current_aliases']:
                    self.writeInt(motbin_ptr + alias_offset, alias, 2)
                    alias_offset += 2
            if 'unknown_aliases' in m:
                alias_offset = 0x120
                for alias in m['unknown_aliases']:
                    self.writeInt(motbin_ptr + alias_offset, alias, 2)
                    alias_offset += 2

        else:  # T6 and later games alias system
            for alias in m['aliases']:
                self.writeInt(motbin_ptr + alias_offset, alias, 2)
                alias_offset += 2

            if 'aliases2' in m:
                alias_offset = 0x108
                for alias in m['aliases2']:
                    self.writeInt(motbin_ptr + alias_offset, alias, 2)
                    alias_offset += 2


def versionMatches(version):
    pos = version.rfind('.')
    exportUpperVersion = version[:pos]

    pos = importVersion.rfind('.')
    importUpperVersion = importVersion[:pos]

    if importUpperVersion == exportUpperVersion and version != importVersion:  # simple warning
        print("\nVersion mismatch: consider exporting the moveset again (not obligated).")
        print("Moveset version: %s. Importer version: %s.\n" %
              (version, importVersion))

    return importUpperVersion == exportUpperVersion


def align8Bytes(value):
    return value + (8 - (value % 8))


def reverseBitOrder(number):
    res = 0
    for i in range(7):  # skip last bit
        bitVal = (number & (1 << i)) != 0
        res |= (bitVal << (7 - i))
    return res


def convertU15(number):
    return (number >> 7) | ((reverseBitOrder(number)) << 24)


def getMovesetTotalSize(m, folderName):
    size = 0
    # size += len(m['character_name']) + 1

    size = align8Bytes(size)
    size += len(m['requirements']) * requirement_size

    size = align8Bytes(size)
    size += len(m['cancel_extradata']) * cancel_extradata_size

    size = align8Bytes(size)
    size += len(m['cancels']) * cancel_size

    size = align8Bytes(size)
    size += len(m['group_cancels']) * cancel_size

    size = align8Bytes(size)
    size += len(m['pushback_extras']) * pushback_extra_size

    size = align8Bytes(size)
    size += len(m['pushbacks']) * pushback_size

    size = align8Bytes(size)
    size += len(m['reaction_list']) * reaction_list_size

    size = align8Bytes(size)
    size += len(m['hit_conditions']) * hit_condition_size

    size = align8Bytes(size)
    size += len(m['extra_move_properties']) * extra_move_property_size

    size = align8Bytes(size)
    size += len(m['move_start_props']) * other_move_props_size

    size = align8Bytes(size)
    size += len(m['move_end_props']) * other_move_props_size

    size = align8Bytes(size)
    size += len(m['voiceclips']) * voiceclip_size

    size = align8Bytes(size)
    # size += sum([k for k in animInfos]) + len(animInfos.keys())
    # for anim in animInfos:
    # size += len(anim) + 1  # filename

    # size = align8Bytes(size)

    # size = align8Bytes(size)
    # for move in m['moves']:
    #     size += len(move['name']) + 1

    size = align8Bytes(size)
    size += len(m['moves']) * move_size

    size = align8Bytes(size)
    size += len(m['input_extradata']) * input_extradata_size

    size = align8Bytes(size)
    size += len(m['input_sequences']) * input_sequence_size

    size = align8Bytes(size)
    size += len(m['projectiles']) * projectile_size

    size = align8Bytes(size)
    size += len(m['throw_extras']) * throw_extras_size

    size = align8Bytes(size)
    size += len(m['throws']) * throws_size

    size = align8Bytes(size)
    size += len(m['parry_related']) * parry_related_size

    size = align8Bytes(size)
    size += len(m['dialogues']) * dialogues_size
    size = align8Bytes(size)
    # for i in range(12):
    #    try:
    #        size += os.path.getsize("%s/mota_%d.bin" % (folderName, i))
    #    except:
    #        pass  # print("Can't open file '%s/mota_%d.bin'" % (folderName, i))

    return size


class MotbinStruct:
    def __init__(self, motbin, folderName, importerObject, animSearchFolder):
        self.importer = importerObject
        self.m = motbin

        self.folderName = folderName

        # self.loadAnimationInfos(animSearchFolder)
        allocSize = getMovesetTotalSize(motbin, folderName)
        head_ptr = self.importer.allocateMem(allocSize)

        self.motbin_ptr = self.importer.allocateMem(0x2e0)
        self.importer.writeBytes(self.motbin_ptr, bytes([0] * 0x2e0))

        self.m = motbin
        self.size = allocSize
        self.head_ptr = head_ptr
        self.curr_ptr = self.head_ptr

        self.cancel_ptr = 0
        self.grouped_cancel_ptr = 0
        self.requirements_ptr = 0
        self.movelist_ptr = 0
        # self.animation_ptr = 0
        self.movelist_names_ptr = 0
        self.animation_names_ptr = 0
        self.extra_data_ptr = 0
        self.reaction_list_ptr = 0
        self.hit_conditions_ptr = 0
        self.pushback_ptr = 0
        self.pushback_extras_ptr = 0
        self.extra_move_properties_ptr = 0
        self.move_start_props_ptr = 0
        self.move_end_props_ptr = 0
        self.voiceclip_ptr = 0
        self.input_extradata_ptr = 0
        self.input_sequences_ptr = 0
        self.projectile_ptr = 0
        self.throw_extras_ptr = 0
        self.throws_ptr = 0
        self.dialogues_ptr = 0
        self.dialogues_count = 0

        self.mota_list = []
        self.move_names_table = {}
        self.animation_table = {}

    def getCurrOffset(self):
        return self.curr_ptr - self.head_ptr

    def isDataFittable(self, size):
        if not (self.getCurrOffset() + size) <= self.size:
            print("Sum: ", self.getCurrOffset() + size)
            print("Self Size: ", self.size)
        return (self.getCurrOffset() + size) <= self.size

    def writeBytes(self, data):
        data_len = len(data)
        if not self.isDataFittable(data_len):
            raise

        dataPtr = self.curr_ptr
        self.importer.writeBytes(dataPtr, data)
        self.curr_ptr += data_len
        return dataPtr

    def writeString(self, text):
        text_len = len(text)
        if not self.isDataFittable(text_len):
            raise

        textAddr = self.curr_ptr
        self.importer.writeString(textAddr, text)
        self.curr_ptr += text_len + 1
        return textAddr

    def writeInt(self, value, bytes_length):
        if not self.isDataFittable(bytes_length):
            raise

        valueAddr = self.curr_ptr
        self.importer.writeInt(valueAddr, value & (
            2 ** (8 * bytes_length)) - 1, bytes_length)
        self.curr_ptr += bytes_length
        return valueAddr

    # Automatically writes a fallback value if not present
    def safeWriteInt(self, obj, key, size, fallback = 0):
        value = obj[key] if key in obj else fallback
        return self.writeInt(value, size)

    def align(self):
        offset = (8 - (self.curr_ptr % 8))
        if not self.isDataFittable(offset):
            raise
        self.curr_ptr += offset
        return self.curr_ptr

    def skip(self, offset):
        if not self.isDataFittable(offset):
            raise

        self.curr_ptr += offset
        return self.curr_ptr

    def loadAnimationInfos(self, animSearchFolder):
        if self.m['version'] == "Tekken8":
            print("Animation info not available for Tekken 8, skipping...")
            return
        else:
            anim_names = set([move['anim_name'] for move in self.m['moves']])
            animMapping = {anim: None for anim in anim_names}

            animFolder = "%s/anim" % (self.folderName)
            try:
                existingAnims = [a[:-4]
                                 for a in os.listdir(animFolder) if a.endswith('.bin')]
            except:
                existingAnims = []

            try:
                prefix = self.folderName.split(
                    "\\")[-1].split("//")[-1].split("_")[0] + '_'
                searchFolders = [animSearchFolder + '/' + c for c in os.listdir(
                    animSearchFolder) if os.path.isdir(animSearchFolder + c) if c.startswith(prefix)]
                searchFolders += [animSearchFolder + '/' + c for c in os.listdir(
                    animSearchFolder) if os.path.isdir(animSearchFolder + c) if not c.startswith(prefix)]
            except:
                searchFolders = [animSearchFolder + '/' + c for c in os.listdir(
                    animSearchFolder) if os.path.isdir(animSearchFolder + c)]

            for anim in anim_names:
                if anim not in existingAnims:
                    try:
                        for char in searchFolders:
                            folder = "%s/anim" % (char)
                            if os.path.exists("%s/%s.bin" % (folder, anim)):
                                size = os.path.getsize(
                                    '%s/%s.bin' % (folder, anim))
                                animMapping[anim] = {
                                    'folder': folder, 'size': size}
                                break
                    except:
                        pass
                else:
                    size = os.path.getsize('%s/%s.bin' % (animFolder, anim))
                    animMapping[anim] = {'folder': animFolder, 'size': size}

            self.animMapping = animMapping

    def getCancelFromId(self, idx):
        if self.cancel_ptr == 0:
            return 0
        return self.cancel_ptr + (idx * cancel_size)

    def getRequirementFromId(self, idx):
        if self.requirements_ptr == 0:
            return 0
        return self.requirements_ptr + (idx * requirement_size)

    def getCancelExtradataFromId(self, idx):
        if self.extra_data_ptr == 0:
            return 0
        return self.extra_data_ptr + (idx * 4)

    def getThrowExtraFromId(self, idx):
        if self.throw_extras_ptr == 0:
            return 0
        return self.throw_extras_ptr + (idx * throw_extras_size)

    def getReactionListFromId(self, idx):
        if self.reaction_list_ptr == 0:
            return 0
        return self.reaction_list_ptr + (idx * reaction_list_size)

    def getExtraMovePropertiesFromId(self, idx):
        if self.extra_move_properties_ptr == 0 or idx == -1:
            return 0
        return self.extra_move_properties_ptr + (idx * extra_move_property_size)

    def getMoveStartPropertiesFromId(self, idx):
        if self.move_start_props_ptr == 0 or idx == -1:
            return 0
        return self.move_start_props_ptr + (idx * other_move_props_size)

    def getMoveEndPropertiesFromId(self, idx):
        if self.move_start_props_ptr == 0 or idx == -1:
            return 0
        return self.move_end_props_ptr + (idx * other_move_props_size)

    def getVoiceclipFromId(self, idx):
        if self.voiceclip_ptr == 0 or idx == -1:
            return 0
        return self.voiceclip_ptr + (idx * voiceclip_size)

    def getHitConditionFromId(self, idx):
        if self.hit_conditions_ptr == 0:
            return 0
        return self.hit_conditions_ptr + (idx * hit_condition_size)

    def getPushbackExtraFromId(self, idx):
        if self.pushback_ptr == 0:
            return 0
        return self.pushback_extras_ptr + (idx * pushback_extra_size)

    def getPushbackFromId(self, idx):
        if self.pushback_ptr == 0:
            return 0
        return self.pushback_ptr + (idx * pushback_size)

    def getInputExtradataFromId(self, idx):
        if self.input_extradata_ptr == 0:
            return 0
        return self.input_extradata_ptr + (idx * input_extradata_size)

    def forbidCancel(self, move_id, groupedCancels=False):
        cancel_list = self.m['group_cancels' if groupedCancels else 'cancels']
        cancel_head_ptr = self.grouped_cancel_ptr if groupedCancels else self.cancel_ptr

        if cancel_head_ptr == 0:
            return

        cancels_toedit = [(i, c) for i, c in enumerate(
            cancel_list) if c['move_id'] == move_id]

        for i, cancel in cancels_toedit:
            addr = cancel_head_ptr + (i * cancel_size)
            self.importer.writeInt(addr, 0xFFFFFFFFFFFFFFFF, 8)

    def allocateInputExtradata(self):
        if self.input_extradata_ptr != 0:
            return
        self.input_extradata_ptr = self.align()

        for extradata in self.m['input_extradata']:
            self.writeInt(extradata['u1'], 4)
            self.writeInt(extradata['u2'], 4)

        return self.input_extradata_ptr, len(self.m['input_extradata'])

    def allocateInputSequences(self):
        if self.input_sequences_ptr != 0:
            return
        self.input_sequences_ptr = self.align()

        for input_sequence in self.m['input_sequences']:
            self.writeInt(input_sequence['u1'], 2)
            self.writeInt(input_sequence['u2'], 2)
            self.writeInt(input_sequence['u3'], 4)
            extradata_addr = self.getInputExtradataFromId(
                input_sequence['extradata_idx'])
            self.writeInt(extradata_addr, 8)

        return self.input_sequences_ptr, len(self.m['input_sequences'])

    def allocateRequirements(self):
        if self.requirements_ptr != 0:
            return
        print("Allocating requirements...")
        self.requirements_ptr = self.align()
        requirements = self.m['requirements']
        requirement_count = len(requirements)

        if self.m['version'] != "Tekken8":
            for i, requirement in enumerate(requirements):
                req, param = getRequirementAlias(
                    self.m['version'], requirement['req'], requirement['param'])
                requirements[i]['req'] = req
                requirements[i]['param'] = param

        applyGlobalRequirementAliases(requirements)

        for i, requirement in enumerate(requirements):
            # The order in which these 4-byte values will be written
            keys = [
                "req",
                "param",
                "param2",
                "param3",
                "param4"
            ]
            for key in keys:
                # if the value doesn't exist, simply write a 0 there
                value = requirement[key] if key in requirement else 0
                self.writeInt(value, 4)

        return self.requirements_ptr, requirement_count

    def allocateCancelExtradata(self):
        if self.extra_data_ptr != 0:
            return
        print("Allocating cancel extradatas...")
        self.extra_data_ptr = self.align()

        for c in self.m['cancel_extradata']:
            self.writeInt(c, 4)

        return self.extra_data_ptr, len(self.m['cancel_extradata'])

    def allocateVoiceclipIds(self):
        if self.voiceclip_ptr != 0:
            return
        print("Allocating voiceclips IDs...")
        self.voiceclip_ptr = self.align()

        for voiceclip in self.m['voiceclips']:
            # The order in which these 4-byte values will be written
            keys = ["val1", "val2", "val3"]
            for key in keys:
                # if the value doesn't exist, simply write a 0 there
                value = voiceclip[key] if key in voiceclip else 0
                self.writeInt(value, 4)

        return self.voiceclip_ptr, len(self.m['voiceclips'])

    def allocateCancels(self, cancels, grouped=False):
        if grouped:
            print("Allocating grouped cancels...")
            self.grouped_cancel_ptr = self.align()
        else:
            print("Allocating cancels...")
            self.cancel_ptr = self.align()
        cancel_count = len(cancels)

        for cancel in cancels:
            self.writeInt(cancel['command'], 8)

            requirements_addr = self.getRequirementFromId(
                cancel['requirement_idx'])
            self.writeInt(requirements_addr, 8)

            extraDataAddr = self.getCancelExtradataFromId(
                cancel['extradata_idx'])
            self.writeInt(extraDataAddr, 8)

            self.writeInt(cancel['frame_window_start'], 4)
            self.writeInt(cancel['frame_window_end'], 4)
            self.writeInt(cancel['starting_frame'], 4)
            self.writeInt(cancel['move_id'], 2)
            self.writeInt(cancel['cancel_option'], 2)

        return self.cancel_ptr if not grouped else self.grouped_cancel_ptr, cancel_count

    def allocatePushbackExtras(self):
        print("Allocating pushback extradata...")
        self.pushback_extras_ptr = self.align()

        for extra in self.m['pushback_extras']:
            self.writeInt(extra, 2)

        return self.pushback_extras_ptr, len(self.m['pushback_extras'])

    def allocatePushbacks(self):
        print("Allocating pushbacks...")
        self.pushback_ptr = self.align()

        for pushback in self.m['pushbacks']:
            self.writeInt(pushback['val1'], 2)
            self.writeInt(pushback['val2'], 2)
            self.writeInt(pushback['val3'], 4)
            self.writeInt(self.getPushbackExtraFromId(
                pushback['pushbackextra_idx']), 8)

        return self.pushback_ptr, len(self.m['pushbacks'])

    def allocateReactionList(self):
        print("Allocating reaction list...")
        self.reaction_list_ptr = self.align()

        for reaction_list in self.m['reaction_list']:
            self.importer.writeBytes(
                self.curr_ptr, bytes([0] * reaction_list_size))

            for pushback in reaction_list['pushback_indexes']:
                self.writeInt(self.getPushbackFromId(pushback), 8)

            # self.skip(0x8) unused
            self.writeInt(reaction_list['front_direction'], 2)
            self.writeInt(reaction_list['back_direction'], 2)
            self.writeInt(reaction_list['left_side_direction'], 2)
            self.writeInt(reaction_list['right_side_direction'], 2)
            self.writeInt(reaction_list['front_counterhit_direction'], 2)
            self.writeInt(reaction_list['downed_direction'], 2)
            self.writeInt(reaction_list['front_rotation'], 2)
            self.writeInt(reaction_list['back_rotation'], 2)
            self.writeInt(reaction_list['left_side_rotation'], 2)
            self.writeInt(reaction_list['right_side_rotation'], 2)
            # aka front_counterhit_rotation
            self.writeInt(reaction_list['vertical_pushback'], 2)
            self.writeInt(reaction_list['downed_rotation'], 2)
            self.writeInt(reaction_list['standing'], 2)
            self.writeInt(reaction_list['crouch'], 2)
            self.writeInt(reaction_list['ch'], 2)
            self.writeInt(reaction_list['crouch_ch'], 2)
            self.writeInt(reaction_list['left_side'], 2)
            self.writeInt(reaction_list['left_side_crouch'], 2)
            self.writeInt(reaction_list['right_side'], 2)
            self.writeInt(reaction_list['right_side_crouch'], 2)
            self.writeInt(reaction_list['back'], 2)
            self.writeInt(reaction_list['back_crouch'], 2)
            self.writeInt(reaction_list['block'], 2)
            self.writeInt(reaction_list['crouch_block'], 2)
            self.writeInt(reaction_list['wallslump'], 2)
            self.writeInt(reaction_list['downed'], 2)
            self.skip(4)  # unused

        return self.reaction_list_ptr, len(self.m['reaction_list'])

    def allocateHitConditions(self):
        print("Allocating hit conditions...")
        self.hit_conditions_ptr = self.align()
        for hit_condition in self.m['hit_conditions']:
            requirement_addr = self.getRequirementFromId(
                hit_condition['requirement_idx'])
            reaction_list_addr = self.getReactionListFromId(
                hit_condition['reaction_list_idx'])
            self.writeInt(requirement_addr, 8)
            self.writeInt(hit_condition['damage'], 4)
            self.writeInt(0, 4)
            self.writeInt(reaction_list_addr, 8)

        return self.hit_conditions_ptr, len(self.m['hit_conditions'])

    def allocateProjectiles(self):
        print("Allocating projectiles...")
        self.projectile_ptr = self.align()

        for p in self.m['projectiles']:
            curr = self.curr_ptr
            self.importer.writeBytes(
                self.curr_ptr, bytes([0] * projectile_size))

            for value in p['u1']:
                self.writeInt(value, 4)

            on_hit_addr = 0
            cancel_addr = 0
            if p['hit_condition_idx'] != -1:
                on_hit_addr = self.getHitConditionFromId(
                    p['hit_condition_idx'])
            if p['cancel_idx'] != -1:
                cancel_addr = self.getCancelFromId(p['cancel_idx'])
            self.writeInt(on_hit_addr, 8)
            self.writeInt(cancel_addr, 8)

            for value in p['u2']:
                self.writeInt(value, 4)

        return self.projectile_ptr, len(self.m['projectiles'])

    def allocateThrowExtras(self):
        print("Allocating throw extras...")
        self.throw_extras_ptr = self.align()

        for t in self.m['throw_extras']:
            self.writeInt(t['u1'], 4)
            for short in t['u2']:
                self.writeInt(short, 2)

        return self.throw_extras_ptr, len(self.m['throw_extras'])

    def allocateThrows(self):
        print("Allocating throws...")
        self.throws_ptr = self.align()

        for t in self.m['throws']:
            self.writeInt(t['u1'], 8)
            extra_addr = self.getThrowExtraFromId(t['throwextra_idx'])
            self.writeInt(extra_addr, 8)

        return self.throws_ptr, len(self.m['throws'])

    def allocateParryRelated(self):
        print("Allocating parry-related...")
        self.parry_related_ptr = self.align()

        for value in self.m['parry_related']:
            self.writeInt(value, 4)

        return self.parry_related_ptr, len(self.m['parry_related'])

    def allocateExtraMoveProperties(self):
        print("Allocating extra move properties...")
        self.extra_move_properties_ptr = self.align()

        for prop in self.m['extra_move_properties']:
            keys = ['type', '_0x4', 'requirement_idx', 'id', 'value', 'value2', 'value3', 'value4', 'value5']
            for key in keys:
                value = prop[key] if key in prop else 0
                size = 4
                if key == 'requirement_idx':
                    value = self.getRequirementFromId(value)
                    size = 8
                self.writeInt(value, size)

        return self.extra_move_properties_ptr, len(self.m['extra_move_properties'])

    def allocateMoveStartProperties(self):
        print("Allocating move start properties...")
        self.move_start_props_ptr = self.align()

        for prop in self.m['move_start_props']:
            keys = ['id', 'value', 'value2', 'value3', 'value4', 'value5']
            requirements_addr = self.getRequirementFromId(prop['requirement_idx'])
            self.writeInt(requirements_addr, 8)
            for key in keys:
                self.writeInt(prop[key] if key in prop else 0, 4)

        return self.move_start_props_ptr, len(self.m['move_start_props'])

    def allocateMoveEndProperties(self):
        print("Allocating move end properties...")
        self.move_end_props_ptr = self.align()

        for prop in self.m['move_end_props']:
            keys = ['id', 'value', 'value2', 'value3', 'value4', 'value5']
            requirements_addr = self.getRequirementFromId(prop['requirement_idx'])
            self.writeInt(requirements_addr, 8)
            for key in keys:
                self.writeInt(prop[key] if key in prop else 0, 4)

        return self.move_end_props_ptr, len(self.m['move_end_props'])

    def allocateDialogueHandlers(self):
        print("Allocating dialogue managers...")
        self.dialogues_ptr = self.align()

        for handler in self.m['dialogues']:
            requirements_addr = self.getRequirementFromId(handler['requirement_idx'])
            self.safeWriteInt(handler, 'type', 2)
            self.safeWriteInt(handler, 'id', 2)
            self.safeWriteInt(handler, '_0x4', 4)
            self.writeInt(requirements_addr, 8)
            self.safeWriteInt(handler, 'voiceclip_key', 4)
            self.safeWriteInt(handler, 'facial_anim_idx', 4, -1)

        return self.dialogues_ptr, len(self.m['dialogues'])

    def allocateAnimations(self):
        print("Allocating animations is not available in this build, skipping...")
        # self.animation_names_ptr = self.align()
        # self.animation_table = {
        #     name: {'name_ptr': self.writeString(name)} for name in self.animMapping}

        # self.animation_ptr = self.align()
        # for name in self.animMapping:
        #     try:
        #         with open("%s/%s.bin" % (self.animMapping[name]['folder'], name), "rb") as f:
        #            self.animation_table[name]['data_ptr'] = self.writeBytes(
        #               f.read())
        #    except Exception as e:
        #        print(e)
        #        self.animation_table[name]['data_ptr'] = 0
        #        print("Warning: animation %s.bin missing from the anim folder, this moveset might crash" % (
        #            name), file=sys.stderr)

    def allocateMota(self):
        if self.m['version'] == "Tekken8":
            print("Mota allocation not available for Tekken 8, skipping...")
            return
        else:
            if len(self.mota_list) != 0:
                return
            self.align()

            for i in range(12):
                try:
                    with open("%s/mota_%d.bin" % (self.folderName, i), "rb") as f:
                        motaBytes = f.read()

                        if motaBytes[0:4] == b'MOTA':
                            motaAddr = self.curr_ptr
                        else:
                            motaAddr = 0
                            # print("DEBUG: Mota %d not valid, not importing" % i)

                        self.writeBytes(motaBytes)
                        self.mota_list.append(motaAddr)
                except:
                    self.mota_list.append(0)
                    # print("Warning: impossible to import MOTA %d" % (i))

    def allocateMoves(self):
        self.allocateAnimations()

        print("Allocating moves...")
        self.movelist_names_ptr = self.align()
        moves = self.m['moves']
        moveCount = len(moves)

        # self.move_names_table = {move['name']: self.writeString(move['name']) for move in moves}

        forbiddenMoveIds = []

        self.movelist_ptr = self.align()
        for i, move in enumerate(moves):
            if move['name'] in forbiddenMoves:
                forbiddenMoveIds.append(i)

            # name_addr = self.move_names_table.get(move['name'], 0)
            # anim_dict = self.animation_table.get(move['anim_name'], None)
            # anim_name = anim_dict['name_ptr']
            # anim_ptr = anim_dict['data_ptr']

            self.writeInt(move['name_key'], 4)  # 0x0
            self.writeInt(move['anim_key'], 4)  # 0x4
            self.writeInt(placeholder_address, 8)  # 0x8
            self.writeInt(placeholder_address, 8)  # 0x10
            self.writeInt(move['anim_addr_enc1'], 4)  # 0x18
            self.writeInt(move['anim_addr_enc2'], 4)  # 0x1C
            self.writeInt(move['vuln'], 4)  # 0x20
            self.writeInt(move['hitlevel'], 4)  # 0x24
            self.writeInt(self.getCancelFromId(move['cancel_idx']), 8)  # 0x28
            self.writeInt(0, 8)  # 0x30
            self.writeInt(0, 8)  # 0x38
            self.writeInt(move['u2'], 8)  # 0x40
            self.writeInt(move['u3'], 8)  # 0x48
            self.writeInt(move['u4'], 8)  # 0x50
            self.writeInt(move['u6'], 4)  # 0x58
            self.writeInt(move['transition'], 2)  # 0x5C
            self.writeInt(move['u7'], 2)  # 0x5E
            self.writeInt(move['_0x60'] if '_0x60' in move else 0, 4)  # 0x60
            self.writeInt(move['ordinal_id'] if 'ordinal_id' in move else 0, 4)  # 0x64
            on_hit_addr = self.getHitConditionFromId(move['hit_condition_idx'])
            self.writeInt(on_hit_addr, 8)  # 0x68
            self.writeInt(move['_0x70'], 4)  # 0x70
            self.writeInt(move['_0x74'], 4)  # 0x74
            self.writeInt(move['anim_max_len'], 4)  # 0x78

            if self.m['version'] == "Tag2" or self.m['version'] == "Revolution":
                move['u15'] = convertU15(move['u15'])

            self.writeInt(move['u10'], 4)  # 0x7C airborne_start
            self.writeInt(move['u11'], 4)  # 0x80 airborne_end
            self.writeInt(move['u12'], 4)  # 0x84 ground_fall

            voiceclip_addr = self.getVoiceclipFromId(move['voiceclip_idx'])
            extra_properties_addr = self.getExtraMovePropertiesFromId(
                move['extra_properties_idx'])
            move_start_properties_addr = self.getMoveStartPropertiesFromId(
                move['move_start_properties_idx'])
            move_end_properties_addr = self.getMoveEndPropertiesFromId(
                move['move_end_properties_idx'])

            self.writeInt(voiceclip_addr, 8)  # 0x88
            self.writeInt(extra_properties_addr, 8)  # 0x90
            self.writeInt(move_start_properties_addr, 8)  # 0x98
            self.writeInt(move_end_properties_addr, 8)  # 0xA0
            self.writeInt(move['u15'], 4)  # 0xA8
            self.writeInt(move['_0xAC'], 4)  # 0xAC
            self.writeInt(move['first_active_frame'], 4)  # 0xB0
            self.writeInt(move['last_active_frame'], 4)  # 0xB4
            self.writeInt(move['first_active_frame1'], 4)  # 0xB8
            self.writeInt(move['last_active_frame1'], 4)  # 0xBC
            self.writeInt(move['hitbox_location1'], 4)  # 0xC0

            # 0xC4 to 0xE8
            for value in move['unk1']:
                self.writeInt(value, 4)

            self.writeInt(move['first_active_frame2'], 4)  # 0xE8
            self.writeInt(move['last_active_frame2'], 4)  # 0xEC
            self.writeInt(move['hitbox_location2'], 4)  # 0xF0

            # 0xF4 to 0x114
            for value in move['unk2']:
                self.writeInt(value, 4)

            # 0x118 to 0x148
            self.writeInt(move['first_active_frame3'], 4)  # 0x118
            self.writeInt(move['last_active_frame3'], 4)  # 0x11C
            self.writeInt(move['hitbox_location3'], 4)  # 0x120
            for value in move['unk3']:
                self.writeInt(value, 4)

            # 0x148 to 0x214
            for value in move['unk4']:
                self.writeInt(value, 4)

            self.writeInt(move['u16'], 2)  # 0x214
            self.writeInt(move['u17'], 2)  # 0x216

            # 0x218 - 0x39C
            for value in move['unk5']:
                self.writeInt(value, 4)

            self.writeInt(move['u18'], 4)  # 0x39C

        for move_id in forbiddenMoveIds:
            self.forbidCancel(move_id, groupedCancels=True)
            self.forbidCancel(move_id, groupedCancels=False)

        return self.movelist_ptr, moveCount

    def applyCharacterIDAliases(self, playerAddr):
        currentChar = self.importer.readInt(
            playerAddr + game_addresses['t8_chara_id_offset'])

        movesetCharId = getCharacteridAlias(
            self.m['version'], self.m['character_id'])

        for i, requirement in enumerate(self.m['requirements']):
            req, param = requirement['req'], requirement['param']

            if req == 220:  # Is current char specific ID
                charId = currentChar if param == movesetCharId else currentChar + 10
                self.importer.writeInt(
                    self.requirements_ptr + (i * 8) + 4, charId, 4)  # force valid

    def applyMotaOffsets(self):
        for i, motaAddr in enumerate(self.mota_list):
            self.importer.writeInt(
                self.motbin_ptr + 0x280 + (i * 8), motaAddr, 8)

    def copyMotaOffsets(self, source_motbin_ptr=None, playerAddr=None):
        if source_motbin_ptr == None and playerAddr == None:
            raise Exception("copyMotaOffsets: No valid address provided")

        if source_motbin_ptr == None:
            source_motbin_ptr = self.importer.readInt(
                playerAddr + game_addresses['t8_motbin_offset'], 8)

        offsets = [
            0x280,  # Anims
            0x288,  # Anims (alias 4000)
            0x290,  # Hand
            0x298,  # Hand (alias 4000)
            0x2a0,  # Face
            0x2a8,  # Face (alias 4000)
            0x2b0,  # Wings
            0x2b8,  # Wings (alias 4000)
            0x2c0,  # Camera
            0x2c8,  # Camera (alias 4000)
            0x2d0,
            0x2d8
        ]

        if "mota_type" in self.m:
            mota_type = self.m["mota_type"]
        else:
            mota_type = 780 if self.m['version'] == 'Tekken8' else (1 << 2)
            # 780 has bit 2,3,8 & 9 set, which indicate respective mota

        # excludedOffsets = [0x290, 0x298, 0x2c0, 0x2c8]
        excludedOffsets = [offset for i, offset in enumerate(
            offsets) if mota_type & (1 << i)]

        for idx, offset in enumerate(offsets):
            if (offset not in excludedOffsets) or self.mota_list[idx] == 0:
                offsetBytes = self.importer.readBytes(
                    source_motbin_ptr + offset, 8)
                self.importer.writeBytes(self.motbin_ptr + offset, offsetBytes)

    def updateCameraMotaStaticPointer(self, playerAddr=None):
        if self.m['version'] != 'Tekken8':
            return
        if playerAddr == None:
            raise Exception(
                "updateCameraMotaStaticPointer: No valid address provided")

        mota8_addr = self.importer.readBytes(self.motbin_ptr + 0x2c0, 8)
        mota9_addr = self.importer.readBytes(self.motbin_ptr + 0x2c8, 8)

        static_mota_ptr = playerAddr + game_addresses['t7_camera_mota_offset']
        self.importer.writeBytes(static_mota_ptr, mota8_addr)
        self.importer.writeBytes(static_mota_ptr + 8, mota9_addr)
        return


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: [FOLDER_NAME]")
        os._exit(1)

    TekkenImporter = Importer()
    playerAddress = game_addresses['t8_p1_addr']
    TekkenImporter.importMoveset(playerAddress, sys.argv[1])

    if len(sys.argv) > 2:
        playerAddress += game_addresses['t8_playerstruct_size']
        TekkenImporter.importMoveset(playerAddress, sys.argv[2])
