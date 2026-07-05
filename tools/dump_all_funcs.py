"""Dump ALL real functions with full decompiled code for analysis."""
import json

data = json.load(open(r'c:\git\training_99\reverse_engineering_ref\decompiled\99_metadata.json'))

for func in data['functions'][:25]:  # real functions only
    code = func.get('code', '')
    callees = [c['name'] for c in func.get('callees', [])]
    callers = [c['name'] for c in func.get('callers', [])]
    strings = func.get('strings', [])
    
    print(f"/*=== {func['name']} @ {func['address']} ===*/")
    print(f"/* Signature: {func['signature']} */")
    if strings: print(f"/* Strings: {strings} */")
    print(f"/* Calls: {', '.join(callees) if callees else '(leaf)'} */")
    print(f"/* Called by: {', '.join(callers) if callers else '(entry)'} */")
    print(code or "/* No decompiled code */")
    print()
    print("/*" + "=" * 78 + "*/")
    print()
