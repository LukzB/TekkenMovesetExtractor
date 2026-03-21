import csv
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
_CSV_PATH = os.path.join(_ROOT, 'InterfaceData', 'character_ids.csv')

_code_by_id = {}
_name_by_id = {}
_loaded = False


def _is_header_row(row):
    if not row:
        return False
    return row[0].strip().lower() == 'id'


def _ensure_loaded():
    global _loaded, _code_by_id, _name_by_id
    if _loaded:
        return
    if not os.path.isfile(_CSV_PATH):
        raise FileNotFoundError(
            'Character ID table not found: %s' % _CSV_PATH)
    _code_by_id = {}
    _name_by_id = {}
    with open(_CSV_PATH, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        first = True
        for row_num, row in enumerate(reader, start=1):
            if not row or all(not str(c).strip() for c in row):
                continue
            if first:
                first = False
                if _is_header_row(row):
                    continue
            if len(row) < 3:
                raise ValueError(
                    'character_ids.csv line %d: expected 3 columns, got %d'
                    % (row_num, len(row)))
            try:
                cid = int(row[0].strip())
            except ValueError:
                raise ValueError(
                    'character_ids.csv line %d: invalid id %r'
                    % (row_num, row[0]))
            code = row[1].strip() if len(row) > 1 else ''
            name = row[2].strip() if len(row) > 2 else ''
            if cid in _code_by_id:
                raise ValueError(
                    'character_ids.csv line %d: duplicate id %d'
                    % (row_num, cid))
            _code_by_id[cid] = code
            _name_by_id[cid] = name
    _loaded = True


def get_character_code(char_id):
    _ensure_loaded()
    try:
        cid = int(char_id)
    except (TypeError, ValueError):
        return 'Unknown'
    code = _code_by_id.get(cid)
    if code is None or code == '':
        return 'Unknown'
    return code


def get_tekken8_character_name(char_id):
    _ensure_loaded()
    try:
        cid = int(char_id)
    except (TypeError, ValueError):
        return 'UNKNOWN'
    name = _name_by_id.get(cid)
    if name is None or name == '':
        return 'UNKNOWN'
    return name
