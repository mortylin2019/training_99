import json
data = json.load(open(r'c:\git\training_99\reverse_engineering_ref\decompiled\99_metadata.json'))
for f in data['functions'][:25]:
    code = f.get('code','')
    lines = code.count('\n')
    callee_names = [c['name'] for c in f.get('callees',[])]
    caller_names = [c['name'] for c in f.get('callers',[])]
    print(f"{f['name']:25s} @ {f['address']}  lines={lines:5d}  "
          f"calls={callee_names if callee_names else '(leaf)'}")
