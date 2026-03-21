import struct
import json
import sys
import os

"""
 * jsonToBin.js - Converts a moveset JSON file back to .motbin binary format.
 * Performs the inverse operation of binToJson.js.
 *
 * Usage: python jsonToBin.py <inputJsonPath> [outputPath] [mode]
 *
 * @see binToJson.js - Extraction logic reference
 * @see classes.h - TK__Moveset struct layout
"""

# ========================== Constants ==================================

XOR_KEYS = [
    0x964f5b9e, 0xd88448a2, 0xa84b71e0, 0xa27d5221, 0x9b81329f, 0xadfb76c8,
    0x7def1f1c, 0x7ee2bc2c,
]

N_ALIASES = 60
N_UNK_ALIASES = 36
BASE = 0x318

# Struct sizes (bytes)
SIZES = {
    "TK_Reaction": 0x70,
    "TK_Requirement": 20,
    "TK_HitCondition": 24,
    "TK_Projectile": 0xe0,
    "TK_Pushback": 0x10,
    "TK_Displacement": 2,
    "TK_Cancel": 40,
    "TK_CancelFlags": 4,
    "TK_TimedExtraprops": 40,
    "TK_UntimedExtraprops": 32,
    "TK_Move": 0x448,
    "TK_Voiceclip": 12,
    "TK_InputSequence": 16,
    "TK_Input": 8,
    "TK_ParryableMove": 4,
    "TK_ThrowCameraData": 12,
    "TK_ThrowCameraHeader": 16,
    "TK_DramaDialogue": 24,
}

# Encrypted field offsets in TK_Move (each region is 0x20 bytes)
MOVE_ENCRYPTED_OFFSETS = [0x0, 0x20, 0x58, 0x78, 0xd0, 0xf0]

# ========================== Buffer Writer Helpers ==================================

def write_int8_le(buf, offset, value):
    struct.pack_into('<b', buf, offset, int(value))
    return offset + 1

def write_uint16_le(buf, offset, value):
    struct.pack_into('<H', buf, offset, int(value) & 0xFFFF)
    return offset + 2

def write_uint32_le(buf, offset, value):
    struct.pack_into('<I', buf, offset, int(value) & 0xFFFFFFFF)
    return offset + 4

def write_int32_le(buf, offset, value):
    struct.pack_into('<i', buf, offset, int(value))
    return offset + 4

def write_uint64_le(buf, offset, value):
    struct.pack_into('<Q', buf, offset, int(value) & 0xFFFFFFFFFFFFFFFF)
    return offset + 8

def write_int64_le(buf, offset, value):
    # In Python, struct handles signed 64-bit directly
    struct.pack_into('<q', buf, offset, int(value))
    return offset + 8

"""
 * Encrypts a 32-bit value into a move's encrypted region.
 * XOR is symmetric - same operation as decrypt.
 * Block at blockIdx stores (value ^ key); other blocks store 0x765 + moveIdx.
"""
def encrypt_value(move_bytes, attribute_offset, value, move_idx):
    block_idx = move_idx % 8
    for j in range(len(XOR_KEYS)):
        key = XOR_KEYS[j]
        offset = attribute_offset + j * 4
        to_write = value if j == block_idx else (0x765 + move_idx)
        encrypted = (to_write ^ key) & 0xFFFFFFFF
        # const encrypted = toWrite;
        struct.pack_into('<I', move_bytes, offset, encrypted)
    return attribute_offset + 0x20

# ========================== Struct Writers ==================================

def write_reaction(buf, offset, reaction):
    off = offset
    # pushback_indexes: stored as raw values (indices/offsets) in the binary
    pushback_indexes = reaction.get("pushback_indexes", [])
    for i in range(7):
        val = pushback_indexes[i] if i < len(pushback_indexes) else 0
        off = write_uint64_le(buf, off, val)

    off = write_uint16_le(buf, off, reaction.get("front_direction", 0))
    off = write_uint16_le(buf, off, reaction.get("back_direction", 0))
    off = write_uint16_le(buf, off, reaction.get("left_side_direction", 0))
    off = write_uint16_le(buf, off, reaction.get("right_side_direction", 0))
    off = write_uint16_le(buf, off, reaction.get("front_counterhit_direction", 0))
    off = write_uint16_le(buf, off, reaction.get("downed_direction", 0))
    off = write_uint16_le(buf, off, reaction.get("front_rotation", 0))
    off = write_uint16_le(buf, off, reaction.get("back_rotation", 0))
    off = write_uint16_le(buf, off, reaction.get("left_side_rotation", 0))
    off = write_uint16_le(buf, off, reaction.get("right_side_rotation", 0))
    off = write_uint16_le(buf, off, reaction.get("vertical_pushback", 0))
    off = write_uint16_le(buf, off, reaction.get("downed_rotation", 0))
    off = write_uint16_le(buf, off, reaction.get("standing", 0))
    off = write_uint16_le(buf, off, reaction.get("crouch", 0))
    off = write_uint16_le(buf, off, reaction.get("ch", 0))
    off = write_uint16_le(buf, off, reaction.get("crouch_ch", 0))
    off = write_uint16_le(buf, off, reaction.get("left_side", 0))
    off = write_uint16_le(buf, off, reaction.get("left_side_crouch", 0))
    off = write_uint16_le(buf, off, reaction.get("right_side", 0))
    off = write_uint16_le(buf, off, reaction.get("right_side_crouch", 0))
    off = write_uint16_le(buf, off, reaction.get("back", 0))
    off = write_uint16_le(buf, off, reaction.get("back_crouch", 0))
    off = write_uint16_le(buf, off, reaction.get("block", 0))
    off = write_uint16_le(buf, off, reaction.get("crouch_block", 0))
    off = write_uint16_le(buf, off, reaction.get("wallslump", 0))
    off = write_uint16_le(buf, off, reaction.get("downed", 0))
    off = write_uint16_le(buf, off, 0)
    off = write_uint16_le(buf, off, 0)
    return off

def write_requirement(buf, offset, req):
    offset = write_uint32_le(buf, offset, req.get("req", 0))
    offset = write_uint32_le(buf, offset, req.get("param", 0))
    offset = write_uint32_le(buf, offset, req.get("param2", 0))
    offset = write_uint32_le(buf, offset, req.get("param3", 0))
    offset = write_uint32_le(buf, offset, req.get("param4", 0))
    return offset

def write_hit_condition(buf, offset, hc):
    offset = write_uint64_le(buf, offset, hc.get("requirement_idx", 0))
    offset = write_uint64_le(buf, offset, hc.get("damage", 0))
    offset = write_uint64_le(buf, offset, hc.get("reaction_list_idx", 0))
    return offset

def write_projectile(buf, offset, proj):
    u1 = proj.get("u1", [])
    for i in range(35):
        val = u1[i] if i < len(u1) else 0
        offset = write_uint32_le(buf, offset, val)
    offset = write_uint64_le(buf, offset, proj.get("hit_condition_idx", 0))
    offset = write_uint64_le(buf, offset, proj.get("cancel_idx", 0))
    u2 = proj.get("u2", [])
    for i in range(16):
        val = u2[i] if i < len(u2) else 0
        offset = write_uint32_le(buf, offset, val)
    return offset

def write_pushback(buf, offset, pb):
    offset = write_uint16_le(buf, offset, pb.get("val1", 0))
    offset = write_uint16_le(buf, offset, pb.get("val2", 0))
    offset = write_uint32_le(buf, offset, pb.get("val3", 0))
    offset = write_uint64_le(buf, offset, pb.get("pushbackextra_idx", 0))
    return offset

def write_cancel(buf, offset, cancel):
    offset = write_uint64_le(buf, offset, int(cancel.get("command", 0)))
    offset = write_uint64_le(buf, offset, cancel.get("requirement_idx", 0))
    offset = write_uint64_le(buf, offset, cancel.get("extradata_idx", 0))
    offset = write_int32_le(buf, offset, cancel.get("frame_window_start", 0))
    offset = write_int32_le(buf, offset, cancel.get("frame_window_end", 0))
    offset = write_int32_le(buf, offset, cancel.get("starting_frame", 0))
    offset = write_uint16_le(buf, offset, cancel.get("move_id", 0))
    offset = write_uint16_le(buf, offset, cancel.get("cancel_option", 0))
    return offset

def write_timed_extraprops(buf, offset, prop):
    offset = write_uint32_le(buf, offset, prop.get("type", 0))
    offset = write_uint32_le(buf, offset, prop.get("_0x4", 0))
    offset = write_uint64_le(buf, offset, prop.get("requirement_idx", 0))
    offset = write_uint32_le(buf, offset, prop.get("id", 0))
    offset = write_uint32_le(buf, offset, prop.get("value", 0))
    offset = write_uint32_le(buf, offset, prop.get("value2", 0))
    offset = write_uint32_le(buf, offset, prop.get("value3", 0))
    offset = write_uint32_le(buf, offset, prop.get("value4", 0))
    offset = write_uint32_le(buf, offset, prop.get("value5", 0))
    return offset

def write_untimed_extraprops(buf, offset, prop):
    offset = write_uint64_le(buf, offset, prop.get("requirement_idx", 0))
    offset = write_uint32_le(buf, offset, prop.get("id", 0))
    offset = write_uint32_le(buf, offset, prop.get("value", 0))
    offset = write_uint32_le(buf, offset, prop.get("value2", 0))
    offset = write_uint32_le(buf, offset, prop.get("value3", 0))
    offset = write_uint32_le(buf, offset, prop.get("value4", 0))
    offset = write_uint32_le(buf, offset, prop.get("value5", 0))
    return offset

"""
 * Writes a single TK__Move struct (0x448 bytes).
 *
 * @param {Buffer} buf - Output buffer.
 * @param {number} offset - Byte offset to write at.
 * @param {object} move - Move data from JSON.
 * @param {number} moveIdx - Index of the move (used for encryption).
 * @param {number} [mode=0] - Logic variation flag (e.g. alternate encryption, layout).
"""
def write_move(buf, offset, move, move_idx, mode = 0):
    # mode: reserved for alternate encryption or move layout
    move_bytes = bytearray(SIZES["TK_Move"])

    # Encrypted fields
    off = 0x0
    off = encrypt_value(move_bytes, off, move.get("name_key", 0), move_idx)
    off = encrypt_value(move_bytes, off, move.get("anim_key", 0), move_idx)
    off = write_uint64_le(move_bytes, off, move.get("name_idx", 0))
    off = write_uint64_le(move_bytes, off, move.get("anim_name_idx", 0))
    off = write_uint32_le(move_bytes, off, move.get("anim_addr_enc1", 0) if mode else move_idx)
    off = write_uint32_le(move_bytes, off, move.get("anim_addr_enc2", 0) if mode else 0)
    off = encrypt_value(move_bytes, off, move.get("vuln", 0), move_idx)
    off = encrypt_value(move_bytes, off, move.get("hitlevel", 0), move_idx)
    off = write_uint64_le(move_bytes, off, move.get("cancel_idx", 0))
    off = write_uint64_le(move_bytes, off, move.get("cancel1_addr", 0))
    off = write_uint64_le(move_bytes, off, move.get("u1", 0))
    off = write_uint64_le(move_bytes, off, move.get("u2", 0))
    off = write_uint64_le(move_bytes, off, move.get("u3", 0))
    off = write_uint64_le(move_bytes, off, move.get("u4", 0))
    off = write_uint32_le(move_bytes, off, move.get("u6", 0))
    off = write_uint16_le(move_bytes, off, move.get("transition", 0))
    off = write_uint16_le(move_bytes, off, move.get("_0xCE", 0))
    off = encrypt_value(move_bytes, off, move.get("_0xD0", 0), move_idx)
    off = encrypt_value(move_bytes, off, move.get("ordinal_id", 0), move_idx)

    # OLD. KEEPSAKE.
    # encrypt_value(move_bytes, 0x0, move.get("name_key", 0), move_idx)
    # encrypt_value(move_bytes, 0x20, move.get("anim_key", 0), move_idx)
    # encrypt_value(move_bytes, 0x58, move.get("vuln", 0), move_idx)
    # encrypt_value(move_bytes, 0x78, move.get("hitlevel", 0), move_idx)
    # encrypt_value(move_bytes, 0xd0, move.get("_0xD0", 0), move_idx)
    # encrypt_value(move_bytes, 0xf0, move.get("ordinal_id", 0), move_idx)

    def to_u64(v):
        if v is None or v < 0:
            return 0xffffffffffffffff
        return int(v) & 0xffffffffffffffff

    off = write_uint64_le(move_bytes, off, move.get("hit_condition_idx", 0))
    off = write_uint32_le(move_bytes, off, move.get("_0x118", 0))
    off = write_uint32_le(move_bytes, off, move.get("_0x11C", 0))
    off = write_uint32_le(move_bytes, off, move.get("anim_max_len", 0) if mode else 0)
    off = write_uint32_le(move_bytes, off, move.get("airborne_start", 0))
    off = write_uint32_le(move_bytes, off, move.get("airborne_end", 0))
    off = write_uint32_le(move_bytes, off, move.get("ground_fall", 0))

    off = write_uint64_le(move_bytes, off, to_u64(move.get("voiceclip_idx")))
    off = write_uint64_le(move_bytes, off, to_u64(move.get("extra_properties_idx")))
    off = write_uint64_le(move_bytes, off, to_u64(move.get("move_start_properties_idx")))
    off = write_uint64_le(move_bytes, off, to_u64(move.get("move_end_properties_idx")))

    off = write_uint32_le(move_bytes, off, move.get("u15", 0))
    off = write_uint32_le(move_bytes, off, move.get("_0x154", 0))
    off = write_uint32_le(move_bytes, off, move.get("first_active_frame", 0))
    off = write_uint32_le(move_bytes, off, move.get("last_active_frame", 0))

    # Hitboxes
    for i in range(8):
        hb_key = f"hitbox{i + 1}"
        hb = move.get(hb_key, {})
        
        faf_key = f"{hb_key}_first_active_frame"
        laf_key = f"{hb_key}_last_active_frame"
        loc_key = f"{hb_key}_location"
        floats_key = f"{hb_key}_related_floats"

        off = write_uint32_le(move_bytes, off, hb.get("first_active_frame", move.get(faf_key, 0)))
        off = write_uint32_le(move_bytes, off, hb.get("last_active_frame", move.get(laf_key, 0)))
        off = write_uint32_le(move_bytes, off, hb.get("location", move.get(loc_key, 0)))
        
        floats = hb.get("related_floats", move.get(floats_key, []))
        for j in range(9):
            val = floats[j] if j < len(floats) else 0
            off = write_uint32_le(move_bytes, off, val)

    off = write_uint16_le(move_bytes, off, move.get("u16", 0))
    off = write_uint16_le(move_bytes, off, move.get("u17", 0))

    unk5 = move.get("unk5", [])
    for i in range(88):
        val = unk5[i] if i < len(unk5) else 0
        off = write_uint32_le(move_bytes, off, val)

    off = write_uint32_le(move_bytes, off, move.get("u18", 0))

    buf[offset : offset + SIZES["TK_Move"]] = move_bytes
    return offset + SIZES["TK_Move"]

def write_voiceclip(buf, offset, vc):
    offset = write_uint32_le(buf, offset, vc.get("val1", 0))
    offset = write_uint32_le(buf, offset, vc.get("val2", 0))
    offset = write_uint32_le(buf, offset, vc.get("val3", 0))
    return offset

def write_input_sequence(buf, offset, seq):
    offset = write_uint16_le(buf, offset, seq.get("u1", 0))
    offset = write_uint16_le(buf, offset, seq.get("u2", 0))
    offset = write_uint32_le(buf, offset, seq.get("u3", 0))
    offset = write_uint64_le(buf, offset, seq.get("extradata_idx", 0))
    return offset

def write_input(buf, offset, input_data):
    offset = write_uint32_le(buf, offset, input_data.get("u1", 0))
    offset = write_uint32_le(buf, offset, input_data.get("u2", 0))
    return offset

def write_throw_camera_data(buf, offset, t):
    offset = write_uint32_le(buf, offset, t.get("u1", 0))
    u2 = t.get("u2", [])
    for i in range(4):
        val = u2[i] if i < len(u2) else 0
        offset = write_uint16_le(buf, offset, val)
    return offset

def write_throw_camera_header(buf, offset, t):
    offset = write_uint64_le(buf, offset, t.get("u1", 0))
    offset = write_uint64_le(buf, offset, t.get("throwextra_idx", 0))
    return offset

def write_drama_dialogue(buf, offset, d):
    offset = write_uint16_le(buf, offset, d.get("type", 0))
    offset = write_uint16_le(buf, offset, d.get("id", 0))
    offset = write_uint32_le(buf, offset, d.get("_0x4", 0))
    offset = write_uint64_le(buf, offset, d.get("requirement_idx", 0))
    offset = write_uint32_le(buf, offset, d.get("voiceclip_key", 0))
    offset = write_uint32_le(buf, offset, d.get("facial_anim_idx", 0))
    return offset

# ========================== Main Conversion ==================================

"""
 * Computes block offsets for all data sections.
 * @param {object} moveset - Parsed JSON moveset
 * @returns {{ offsets: number[], blockOffsets: object }}
"""
def compute_block_layout(moveset):
    counts = {
        "reaction_list": len(moveset.get("reaction_list", [])),
        "requirements": len(moveset.get("requirements", [])),
        "hit_conditions": len(moveset.get("hit_conditions", [])),
        "projectiles": len(moveset.get("projectiles", [])),
        "pushbacks": len(moveset.get("pushbacks", [])),
        "pushback_extras": len(moveset.get("pushback_extras", [])),
        "cancels": len(moveset.get("cancels", [])),
        "group_cancels": len(moveset.get("group_cancels", [])),
        "cancel_extradata": len(moveset.get("cancel_extradata", [])),
        "extra_move_properties": len(moveset.get("extra_move_properties", [])),
        "move_start_props": len(moveset.get("move_start_props", [])),
        "move_end_props": len(moveset.get("move_end_props", [])),
        "moves": len(moveset.get("moves", [])),
        "voiceclips": len(moveset.get("voiceclips", [])),
        "input_sequences": len(moveset.get("input_sequences", [])),
        "input_extradata": len(moveset.get("input_extradata", [])),
        "parry_related": len(moveset.get("parry_related", [])),
        "throw_extras": len(moveset.get("throw_extras", [])),
        "throws": len(moveset.get("throws", [])),
        "dialogues": len(moveset.get("dialogues", [])),
    }

    block_order = [
        "reaction_list", "requirements", "hit_conditions", "projectiles",
        "pushbacks", "pushback_extras", "cancels", "group_cancels",
        "cancel_extradata", "extra_move_properties", "move_start_props", "move_end_props",
        "moves", "voiceclips", "input_sequences", "input_extradata",
        "parry_related", "throw_extras", "throws", "dialogues",
    ]

    size_map = {
        "reaction_list": SIZES["TK_Reaction"],
        "requirements": SIZES["TK_Requirement"],
        "hit_conditions": SIZES["TK_HitCondition"],
        "projectiles": SIZES["TK_Projectile"],
        "pushbacks": SIZES["TK_Pushback"],
        "pushback_extras": SIZES["TK_Displacement"],
        "cancels": SIZES["TK_Cancel"],
        "group_cancels": SIZES["TK_Cancel"],
        "cancel_extradata": SIZES["TK_CancelFlags"],
        "extra_move_properties": SIZES["TK_TimedExtraprops"],
        "move_start_props": SIZES["TK_UntimedExtraprops"],
        "move_end_props": SIZES["TK_UntimedExtraprops"],
        "moves": SIZES["TK_Move"],
        "voiceclips": SIZES["TK_Voiceclip"],
        "input_sequences": SIZES["TK_InputSequence"],
        "input_extradata": SIZES["TK_Input"],
        "parry_related": SIZES["TK_ParryableMove"],
        "throw_extras": SIZES["TK_ThrowCameraData"],
        "throws": SIZES["TK_ThrowCameraHeader"],
        "dialogues": SIZES["TK_DramaDialogue"],
    }

    offset = BASE
    block_offsets = {}
    for key in block_order:
        block_offsets[key] = offset
        offset += counts[key] * size_map[key]
    return {"blockOffsets": block_offsets, "counts": counts}

"""
 * Writes the TK__Moveset header (0x0 - 0x318).
 *
 * @param {Buffer} buf - Output buffer to write the header into.
 * @param {object} moveset - Parsed JSON moveset (aliases, character_id, _0x4, etc.).
 * @param {Record<string, number>} blockOffsets - Map of block names to their start offsets in the buffer.
 * @param {Record<string, number>} counts - Map of block names to their element counts.
 * @param {number} [mode=0] - Logic variation flag (e.g. alternate layouts, padding).
"""
def write_header(buf, moveset, block_offsets, counts, mode = 0):
    offset = 0
    # 0x00: disable_anim_lookup (2 bytes) - mode 1 sets to 1
    offset = write_uint16_le(buf, offset, 1 if mode else 0)
    offset = write_int8_le(buf, offset, 0) # 0x02: is_written
    offset = write_int8_le(buf, offset, 0) # 0x03: _0x3
    offset = write_uint32_le(buf, offset, moveset.get("_0x4", 0)) # 0x04: _0x4
    offset = write_uint32_le(buf, offset, 4932948) # 0x08: "TEK\0"
    offset = write_uint32_le(buf, offset, 0) # 0x0C: _0xC
    offset = write_uint64_le(buf, offset, 0) # 0x10: character_name_addr
    offset = write_uint64_le(buf, offset, 0) # 0x18: creator_addr
    offset = write_uint64_le(buf, offset, 0) # 0x20: date_addr
    offset = write_uint64_le(buf, offset, 0) # 0x28: fulldate_addr

    # 0x30: aliases
    orig = moveset.get("original_aliases", [])
    curr = moveset.get("current_aliases", [])
    unk = moveset.get("unknown_aliases", [])
    for i in range(N_ALIASES):
        val = orig[i] if i < len(orig) else 0
        offset = write_uint16_le(buf, offset, val)
    for i in range(N_ALIASES):
        val = curr[i] if i < len(curr) else 0
        offset = write_uint16_le(buf, offset, val)
    for i in range(N_UNK_ALIASES):
        val = unk[i] if i < len(unk) else 0
        offset = write_uint16_le(buf, offset, val)

    # 0x160: character_id (stored as (id * 0xffff + 1) for TK_CharId)
    # const charId = moveset.character_id ?? 0;
    # const charIdEnc = charId * 0xffff + 1;
    # writeInt32LE(buf, 0x160, charIdEnc);

    # 0x164-0x167: ordinal_id2 (per classes.h: (-charId)&0xffff | (charId<<16))
    # const ord2 = ((Number(-charId) >>> 0) & 0xffff) | ((charId & 0xffff) << 16);
    # writeUInt32LE(buf, 0x164, ord2);

    # 0x168-0x2a8: block pointers (offset - BASE) and counts
    rl_start = block_offsets.get("reaction_list", 0)
    offset = write_uint64_le(buf, offset, rl_start - BASE)
    offset = write_uint64_le(buf, offset, moveset.get("_string_block_end_offset", 0))
    offset = write_uint64_le(buf, offset, counts.get("reaction_list", 0))

    ptr_pairs = [
        [0x180, "requirements", 0x188],
        [0x190, "hit_conditions", 0x198],
        [0x1a0, "projectiles", 0x1a8],
        [0x1b0, "pushbacks", 0x1b8],
        [0x1c0, "pushback_extras", 0x1c8],
        [0x1d0, "cancels", 0x1d8],
        [0x1e0, "group_cancels", 0x1e8],
        [0x1f0, "cancel_extradata", 0x1f8],
        [0x200, "extra_move_properties", 0x208],
        [0x210, "move_start_props", 0x218],
        [0x220, "move_end_props", 0x228],
        [0x230, "moves", 0x238],
        [0x240, "voiceclips", 0x248],
        [0x250, "input_sequences", 0x258],
        [0x260, "input_extradata", 0x268],
        [0x270, "parry_related", 0x278],
        [0x280, "throw_extras", 0x288],
        [0x290, "throws", 0x298],
        [0x2a0, "dialogues", 0x2a8],
    ]

    # ptr_off and count_off are ignored
    for ptr_off, key, count_off in ptr_pairs:
        block_start = block_offsets.get(key, 0)
        rel_offset = block_start - BASE
        offset = write_uint64_le(buf, offset, rel_offset)
        offset = write_uint64_le(buf, offset, counts.get(key, 0))

    # 0x2b0-0x318: mota pointers (zeros)
    for i in range(13):
        offset = write_uint64_le(buf, offset, 0)
    return offset

"""
 * Converts JSON moveset to binary .motbin buffer.
 * @param {object} moveset - Parsed JSON moveset
 * @param {number} [mode] - Placeholder for logic variations
 * @returns {Buffer}
"""
def json_to_motbin(moveset, mode = 0):
    # mode: placeholder for logic variations (e.g. alternate layouts, padding)
    layout = compute_block_layout(moveset)
    block_offsets = layout["blockOffsets"]
    counts = layout["counts"]
    total_size = block_offsets["dialogues"] + (counts.get("dialogues", 0)) * SIZES["TK_DramaDialogue"]
    buf = bytearray(total_size)

    write_header(buf, moveset, block_offsets, counts, mode)

    off = BASE

    size_map = {
        "reaction_list": SIZES["TK_Reaction"],
        "requirements": SIZES["TK_Requirement"],
        "hit_conditions": SIZES["TK_HitCondition"],
        "projectiles": SIZES["TK_Projectile"],
        "pushbacks": SIZES["TK_Pushback"],
        "pushback_extras": SIZES["TK_Displacement"],
        "cancels": SIZES["TK_Cancel"],
        "group_cancels": SIZES["TK_Cancel"],
        "cancel_extradata": SIZES["TK_CancelFlags"],
        "extra_move_properties": SIZES["TK_TimedExtraprops"],
        "move_start_props": SIZES["TK_UntimedExtraprops"],
        "move_end_props": SIZES["TK_UntimedExtraprops"],
        "moves": SIZES["TK_Move"],
        "voiceclips": SIZES["TK_Voiceclip"],
        "input_sequences": SIZES["TK_InputSequence"],
        "input_extradata": SIZES["TK_Input"],
        "parry_related": SIZES["TK_ParryableMove"],
        "throw_extras": SIZES["TK_ThrowCameraData"],
        "throws": SIZES["TK_ThrowCameraHeader"],
        "dialogues": SIZES["TK_DramaDialogue"],
    }

    block_config = [
        ["reaction_list", write_reaction, moveset.get("reaction_list", [])],
        ["requirements", write_requirement, moveset.get("requirements", [])],
        ["hit_conditions", write_hit_condition, moveset.get("hit_conditions", [])],
        ["projectiles", write_projectile, moveset.get("projectiles", [])],
        ["pushbacks", write_pushback, moveset.get("pushbacks", [])],
        ["pushback_extras", None, moveset.get("pushback_extras", [])],
        ["cancels", write_cancel, moveset.get("cancels", [])],
        ["group_cancels", write_cancel, moveset.get("group_cancels", [])],
        ["cancel_extradata", None, moveset.get("cancel_extradata", [])],
        ["extra_move_properties", write_timed_extraprops, moveset.get("extra_move_properties", [])],
        ["move_start_props", write_untimed_extraprops, moveset.get("move_start_props", [])],
        ["move_end_props", write_untimed_extraprops, moveset.get("move_end_props", [])],
        ["moves", write_move, moveset.get("moves", [])],
        ["voiceclips", write_voiceclip, moveset.get("voiceclips", [])],
        ["input_sequences", write_input_sequence, moveset.get("input_sequences", [])],
        ["input_extradata", write_input, moveset.get("input_extradata", [])],
        ["parry_related", None, moveset.get("parry_related", [])],
        ["throw_extras", write_throw_camera_data, moveset.get("throw_extras", [])],
        ["throws", write_throw_camera_header, moveset.get("throws", [])],
        ["dialogues", write_drama_dialogue, moveset.get("dialogues", [])],
    ]

    for key, writer, arr in block_config:
        arr2 = arr if arr is not None else []
        size = size_map[key]
        for i in range(len(arr2)):
            if key == "moves":
                writer(buf, off, arr2[i], i, mode)
                # TODO: Move post-process
            elif key == "pushback_extras":
                data = arr2[i]
                val = data.get("value", data) if isinstance(data, dict) else data
                write_uint16_le(buf, off, val if val is not None else 0)
            elif key == "cancel_extradata" or key == "parry_related":
                data = arr2[i]
                val = data.get("value", data) if isinstance(data, dict) else data
                write_uint32_le(buf, off, val if val is not None else 0)
            else:
                writer(buf, off, arr2[i])
            off += size

    return buf

# ========================== CLI ==================================

def main():
    args = sys.argv[1:]
    if len(args) < 1:
        print("Usage: python jsonToBin.py <inputJsonPath> [outputPath] [mode]")
        sys.exit(1)

    input_json_path = args[0]
    output_path = args[1] if len(args) > 1 else input_json_path.replace(".json", ".motbin").replace(".JSON", ".motbin")
    mode = int(args[2]) if len(args) > 2 else 0

    moveset = None
    try:
        with open(input_json_path, "r", encoding="utf8") as f:
            raw = f.read()
            moveset = json.loads(raw)
    except Exception as err:
        print(f"Failed to read JSON: {err}")
        sys.exit(1)

    buffer = None
    # buffer = json_to_motbin(moveset, mode)
    try:
        buffer = json_to_motbin(moveset, mode)
    except Exception as err:
        print(f"Conversion failed: {err}")
        if os.environ.get("DEBUG"):
            raise err
        sys.exit(1)

    try:
        with open(output_path, "wb") as f:
            f.write(buffer)
        print(f"Written {len(buffer)} bytes to {output_path}")
    except Exception as err:
        print(f"Failed to write file: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()

