#!/usr/bin/env python3
"""Validate all DSU files"""
import json, os
DIR = r'C:\Users\DELL\textbook-project\kg-schema\samples'

files = ['dsu-samples-001.json','dsu-samples-002.json','dsu-samples-003.json',
         'dsu-samples-004.json','dsu-samples-005.json','dsu-samples-006.json','dsu-samples-007.json']

total = 0
all_ids = []
errors = []

for fn in files:
    path = os.path.join(DIR, fn)
    if not os.path.exists(path):
        errors.append(f'MISSING: {fn}')
        continue
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    n = len(data)
    total += n
    ids = [u['id'] for u in data]
    for uid in ids:
        all_ids.append(uid)
    # Check required fields
    for u in data:
        for req in ['id','disease_side','syndrome_side','bridge','clinical','teaching','metadata']:
            if req not in u:
                errors.append(f'{u["id"]}: missing {req}')
        ds = u.get('disease_side',{})
        if len(ds.get('molecular_targets',[])) < 2:
            errors.append(f'{u["id"]}: <2 molecular targets')
        ss = u.get('syndrome_side',{})
        ft = ss.get('field_theory','')
        if len(ft) < 50:
            errors.append(f'{u["id"]}: field_theory too short ({len(ft)})')
        bb = u.get('bridge',{}).get('biological_basis','')
        if len(bb) < 30:
            errors.append(f'{u["id"]}: biological_basis too short ({len(bb)})')
        t = u.get('teaching',{})
        zr = t.get('sage_ref_zhang','')
        sr = t.get('sage_ref_sun','')
        if not zr: errors.append(f'{u["id"]}: missing sage_ref_zhang')
        if not sr: errors.append(f'{u["id"]}: missing sage_ref_sun')
        tc = t.get('typical_case','')
        if len(tc) < 80: errors.append(f'{u["id"]}: typical_case too short ({len(tc)})')
        tp = t.get('teaching_points',[])
        if len(tp) < 3: errors.append(f'{u["id"]}: <3 teaching_points ({len(tp)})')
        eq = t.get('exam_questions',[])
        if len(eq) < 2: errors.append(f'{u["id"]}: <2 exam_questions ({len(eq)})')
    print(f'{fn}: {n} DSUs, {ids[0]}~{ids[-1]}')

print(f'\nTotal: {total} DSUs across 7 batches')
print(f'ID range: {all_ids[0]} ~ {all_ids[-1]}')

# Check ID continuity
expected = [f'DSU-{i:05d}' for i in range(1, total+1)]
if all_ids == expected:
    print('ID continuity: ✅ All IDs continuous and correct')
else:
    for i, (e, a) in enumerate(zip(expected, all_ids)):
        if e != a:
            print(f'ID gap at pos {i+1}: expected {e}, got {a}')
            break

if errors:
    print(f'\n⚠️ {len(errors)} validation errors:')
    for e in errors[:10]:
        print(f'  - {e}')
else:
    print('Schema: ✅ All DSUs pass basic validation')
