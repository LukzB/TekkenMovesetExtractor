# --- Ton-Chan's Motbin import --- #
# Python 3.6.5

from Addresses import GameAddresses, GameClass, VirtualAllocEx, VirtualFreeEx, GetLastError, MEM_RESERVE, MEM_COMMIT, MEM_DECOMMIT, MEM_RELEASE, PAGE_EXECUTE_READWRITE
from Aliases import getTag2Requirement, getTag2_offset98Alias
import json
import os
import sys

if len(sys.argv) == 1:
    print("Usage: [FOLDER_NAME]")
    os._exit(1)
   
T = GameClass("TekkenGame-Win64-Shipping.exe")
folderName = sys.argv[1]
charaName = folderName[2:]
jsonFilename = "%s.json" % (charaName)

requirement_size = 0x8
cancel_size = 0x28
move_size = 0xb0
reaction_list_size = 0x70
hit_condition_size = 0x18
pushback_size = 0x10
pushback_extra_size = 0x2

def getTag2RequirementAlias(req, param):
    requirement_detail = getTag2Requirement(req)
    if requirement_detail == None:
        return req, param
            
    return requirement_detail['id'], param

def readInt(addr, bytes_length=4):
    return T.readInt(addr, bytes_length)
    
def writeInt(addr, value, bytes_length=0):
    return T.writeInt(addr, value, bytes_length=bytes_length)
    
def writeBytes(addr, data):
    return T.writeBytes(addr, data)
    
def writeString(addr, text):
    return writeBytes(addr, bytes(text + "\x00", 'ascii'))

def allocateMem(allocSize):
    return VirtualAllocEx(T.handle, 0, allocSize, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
    
def writeAliases(motbin_ptr, aliases):
    alias_offset = 0x98
    for alias in aliases:
        writeInt(motbin_ptr + alias_offset, alias, 2)
        alias_offset += 2
    writeInt(motbin_ptr + 0x98, aliases[1], 2)
        
def align8Bytes(value):
    return value + (8 - (value % 8))
    
def getTotalSize(m):
    size = 0
    size += len(m['character_name']) + 1
    size += len(m['creator_name']) + 1
    size += len(m['date']) + 1
    size += len(m['fulldate']) + 1
        
    size = align8Bytes(size)
    size += len(m['requirements']) * 8
        
    size = align8Bytes(size)
    extra_data_list = [cancel['extra_data'] for cancel in m['cancels']]
    extra_data_list += [cancel['extra_data'] for cancel in m['group_cancels']]
    
    size = align8Bytes(size)
    size += len(m['cancels']) * 0x28

    size = align8Bytes(size)
    size += len(m['group_cancels']) * 0x28
    size += len(set(extra_data_list)) * 4
    
    size = align8Bytes(size)
    size += len(m['pushback_extras']) * 0x2
    
    size = align8Bytes(size)
    size += len(m['pushbacks']) * 0x10
    
    size = align8Bytes(size)
    size += len(m['reaction_list']) * 0x70
    
    size = align8Bytes(size)
    size += len(m['hit_conditions']) * 0x18

    size = align8Bytes(size)
    for animName in m['anims']: 
        size += len(animName) + 1
    
    size = align8Bytes(size)
    for anim in m['anims']:
        size += os.path.getsize("%s/anim/%s.bin" % (folderName, anim))

    size = align8Bytes(size)
    for move in m['moves']:
        size += len(move['name']) + 1   
    
    size = align8Bytes(size)
    size += len(m['moves']) * 0xB0
    
    return size
    
class MotbinPtr:
    def __init__(self, motbin):
        allocSize = getTotalSize(m)
        head_ptr = allocateMem(allocSize)
        
        self.m = motbin
        self.size = allocSize
        self.head_ptr = head_ptr
        self.curr_ptr = self.head_ptr
        
        self.cancel_ptr = 0
        self.grouped_cancel_ptr = 0
        self.requirements_ptr = 0
        self.movelist_ptr = 0
        self.animation_ptr = 0
        self.movelist_names_ptr = 0
        self.animation_names_ptr = 0
        self.extra_data_ptr = 0
        self.reaction_list_ptr = 0
        self.hit_conditions_ptr = 0
        self.pushback_ptr = 0
        self.pushback_extras_ptr = 0
        
        self.move_names_table = {}
        self.animation_table = {}
        self.extra_data_table = {}
    
    def getCurrOffset(self):
        return self.curr_ptr - self.head_ptr
     
    def isDataFittable(self, size):
        return (self.getCurrOffset()  + size) <= self.size
        
    def writeBytes(self, data):
        data_len = len(data)
        if not self.isDataFittable(data_len):
            raise
        
        dataPtr = self.curr_ptr
        writeBytes(dataPtr, data)
        self.curr_ptr += data_len
        return dataPtr
        
    def writeString(self, text):
        text_len = len(text)
        if not self.isDataFittable(text_len):
            raise
            
        textAddr = self.curr_ptr
        writeString(textAddr, text)
        self.curr_ptr += text_len + 1
        return textAddr
        
    def writeInt(self, value, bytes_length):
        if not self.isDataFittable(bytes_length):
            raise
            
        valueAddr = self.curr_ptr
        writeInt(valueAddr, value, bytes_length)
        self.curr_ptr += bytes_length
        return valueAddr
        
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
        
    def getCancelFromId(self, idx):
        if self.cancel_ptr == 0:
            return 0
        return self.cancel_ptr + (idx * cancel_size)
        
    def getRequirementFromId(self, idx):
        if self.requirements_ptr == 0:
            return 0
        return self.requirements_ptr + (idx * requirement_size)
        
    def getReactionListFromId(self, idx):
        if self.reaction_list_ptr == 0:
            return 0
        return self.reaction_list_ptr + (idx * reaction_list_size)
        
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
        
    def allocateRequirements(self):
        print("Allocating requirements...")
        self.requirements_ptr = self.align()
        requirements = self.m['requirements']
        requirement_count = len(requirements)
        
        for requirement in requirements:
            req = requirement['req']
            param = requirement['param']
            if self.m['version'] == "Tag2":
                req, param = getTag2RequirementAlias(req, param)
            self.writeInt(req, 4)
            self.writeInt(param, 4)
        
        return self.requirements_ptr, requirement_count
        
    def allocateCancelExtradata(self):
        if self.extra_data_ptr != 0:
            return
        print("Allocating cancels extradata...")
        self.extra_data_ptr = self.align()
        
        extra_data_list = [cancel['extra_data'] for cancel in self.m['cancels']]
        extra_data_list += [cancel['extra_data'] for cancel in self.m['group_cancels']]
        extra_data_list = set(extra_data_list)
        
        self.extra_data_table = {value:self.writeInt(value, 4) for value in extra_data_list}
        
    def allocateCancels(self, cancels, grouped=False):
        self.allocateCancelExtradata()
        
        if grouped:
            print("Allocating grouped cancels...")
            self.grouped_cancel_ptr = self.align()
        else:
            print("Allocating cancels...")
            self.cancel_ptr = self.align()
        cancel_count = len(cancels)
        
        for cancel in cancels:
            self.writeInt(cancel['command'], 8)
            
            requirements_addr = self.getRequirementFromId(cancel['requirement'])
            self.writeInt(requirements_addr, 8)
            
            extraDataAddr = self.extra_data_table.get(cancel['extra_data'], 0)
            self.writeInt(extraDataAddr, 8)
            
            self.writeInt(cancel['frame_window_start'], 4)
            self.writeInt(cancel['frame_window_end'], 4)
            self.writeInt(cancel['starting_frame'], 4)
            self.writeInt(cancel['move_id'], 2)
            self.writeInt(cancel['unknown'], 2)
                
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
            self.writeInt(self.getPushbackExtraFromId(pushback['extra_index']), 8)
        
        return self.pushback_ptr, len(self.m['pushbacks'])
                
    def allocateReactionList(self):
        print("Allocating reaction list...")
        self.reaction_list_ptr = self.align()
        
        for reaction_list in self.m['reaction_list']:
            writeBytes(self.curr_ptr, bytes([0] * reaction_list_size))
            
            for pushback in reaction_list['pushback_indexes']:
                self.writeInt(self.getPushbackFromId(pushback), 8)
                
            self.skip(0x18)
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
            self.skip(4)
        
        return self.reaction_list_ptr, len(self.m['reaction_list'])
        
    def allocateHitConditions(self):
        print("Allocating hit conditions...")
        self.hit_conditions_ptr = self.align()
        
        for hit_condition in self.m['hit_conditions']:
            requirement_addr = self.getRequirementFromId(hit_condition['requirement'])
            reaction_list_addr = self.getReactionListFromId(hit_condition['reaction_list'])
            self.writeInt(requirement_addr, 8)
            self.writeInt(hit_condition['damage'], 4) 
            self.writeInt(0, 4) 
            self.writeInt(reaction_list_addr, 8)
        
        return self.hit_conditions_ptr, len(self.m['hit_conditions'])
        
    def allocateAnimations(self):
        print("Allocating animations...")
        self.animation_names_ptr = self.align()
        self.animation_table = {name:{'name_ptr':self.writeString(name)} for name in self.m['anims']}
        
        self.animation_ptr = self.align()
        for name in self.m['anims']:
            with open("%s/anim/%s.bin" % (folderName, name), "rb") as f:
                self.animation_table[name]['data_ptr'] = self.writeBytes(f.read())
        
    def allocateMoves(self):
        if self.cancel_ptr == 0:
            return
        print("Allocating moves...")
        self.movelist_names_ptr =  self.align()
        moves = self.m['moves']
        moveCount = len(moves)
        
        self.move_names_table = {move['name']:self.writeString(move['name']) for move in moves}
        
        missingAliasList = []
        
        self.movelist_ptr = self.align()
        for move in moves:
            name_addr = self.move_names_table.get(move['name'], 0)
            anim_dict = self.animation_table.get(move['anim_name'], None)
            anim_name, anim_ptr = anim_dict['name_ptr'], anim_dict['data_ptr']
            
            self.writeInt(name_addr, 8)
            self.writeInt(anim_name, 8)
            self.writeInt(anim_ptr, 8)
            self.writeInt(move['vuln'], 4)
            self.writeInt(move['hitlevel'], 4)
            self.writeInt(self.getCancelFromId(move['cancel']), 8)
            
            self.writeInt(move['u1'], 8)
            self.writeInt(move['u2'], 8)
            self.writeInt(move['u3'], 8)
            self.writeInt(move['u4'], 8)
            self.writeInt(move['u5'], 8)
            self.writeInt(move['u6'], 4)
            
            self.writeInt(move['transition'], 2)
            
            self.writeInt(move['u7'], 2)
            self.writeInt(move['u8'], 2)
            self.writeInt(move['u8_2'], 2)
            self.writeInt(move['u9'], 4)
            
            on_hit_addr = self.getHitConditionFromId(move['hit_condition'])
            self.writeInt(on_hit_addr, 8)
            self.writeInt(move['anim_max_len'], 4)
            
            u12, u15 = move['u12'], move['u15']
            if u15 != 0 and self.m['version'] == "Tag2": #Pushback correction
                u15 = getTag2_offset98Alias(u15)
                if u15 == 0:
                    u15 = move['u15']
                    u12 = 0
                    missingAliasList.append(move['u15'])
            
            self.writeInt(move['u10'], 4)
            self.writeInt(move['u11'], 4)
            self.writeInt(u12, 4)
            
            self.writeInt(0, 8) #extra_properties_1
            self.writeInt(0, 8) #extra_properties_1
            
            self.writeInt(move['u13'], 8)
            self.writeInt(move['u14'], 8)
            self.writeInt(u15, 4)
            
            self.writeInt(move['hitbox_location'], 4)
            self.writeInt(move['startup'], 4)
            self.writeInt(move['recovery'], 4)
            
            self.writeInt(move['u16'], 8)
            
        for u15 in list(set(missingAliasList)):
            print("Missing alias for offset 0x98: %d" % (u15))
        
        return self.movelist_ptr, moveCount
        
if __name__ == "__main__":
    motbin_ptr_addr = GameAddresses.a['p1_ptr'] + 0x14a0 #
    motbin_ptr = readInt(motbin_ptr_addr, 8)
    
    m = None
    
    print("Reading %s..." % (jsonFilename))
    with open("%s/%s" % (folderName, jsonFilename), "r") as f:
        m = json.load(f)
        f.close()
        
    p = MotbinPtr(m)
        
    character_name = p.writeString(m['character_name'])
    creator_name = p.writeString(m['creator_name'])
    date = p.writeString(m['date'])
    fulldate = p.writeString(m['fulldate'])
    
    requirements_ptr, requirement_count = p.allocateRequirements()
    cancel_ptr, cancel_count = p.allocateCancels(m['cancels'])
    group_cancel_ptr, group_cancel_count = p.allocateCancels(m['group_cancels'], grouped=True)
    pushback_extras_ptr, pushback_extras_size = p.allocatePushbackExtras()
    pushback_ptr, pushback_list_size = p.allocatePushbacks()
    reaction_list_ptr, reaction_list_count = p.allocateReactionList()
    hit_conditions_ptr, hit_conditions_size = p.allocateHitConditions()
    
    p.allocateAnimations()
    moves_ptr, move_count = p.allocateMoves()
    
    writeInt(motbin_ptr + 0x8, character_name, 8)
    writeInt(motbin_ptr + 0x10, creator_name, 8)
    writeInt(motbin_ptr + 0x18, date, 8)
    writeInt(motbin_ptr + 0x20, fulldate, 8)
    
    writeAliases(motbin_ptr, m['aliases'])
    
    writeInt(motbin_ptr + 0x150, reaction_list_ptr, 8)
    writeInt(motbin_ptr + 0x158, reaction_list_count, 8)
    
    writeInt(motbin_ptr + 0x160, requirements_ptr, 8)
    writeInt(motbin_ptr + 0x168, requirement_count, 8)
    
    writeInt(motbin_ptr + 0x170, hit_conditions_ptr, 8)
    writeInt(motbin_ptr + 0x178, hit_conditions_size, 8)
    
    writeInt(motbin_ptr + 0x190, pushback_ptr, 8)
    writeInt(motbin_ptr + 0x198, pushback_list_size, 8)
    
    writeInt(motbin_ptr + 0x1A0, pushback_extras_ptr, 8)
    writeInt(motbin_ptr + 0x1A8, pushback_extras_size, 8)
    
    writeInt(motbin_ptr + 0x1b0, cancel_ptr, 8)
    writeInt(motbin_ptr + 0x1b8, cancel_count, 8)
    
    writeInt(motbin_ptr + 0x1c0, group_cancel_ptr, 8)
    writeInt(motbin_ptr + 0x1c8, group_cancel_count, 8)
    
    writeInt(motbin_ptr + 0x210, moves_ptr, 8)
    writeInt(motbin_ptr + 0x218, move_count, 8)
    
    print("%s successfully imported in memory." % (jsonFilename))
    print("%d/%d bytes left." % (p.size - (p.curr_ptr - p.head_ptr), p.size))
    

    