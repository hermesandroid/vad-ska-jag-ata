#!/usr/bin/env python3
"""Translate English recipes one at a time (simple text format, no JSON)"""
import json, os, time, urllib.request

with open("recipes.json") as f:
    recipes = json.load(f)

env_path = os.path.expanduser("~/.hermes/.env")
with open(env_path) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY"):
            DK = line.split("=",1)[1].strip()

DS_URL = "https://api.deepseek.com/chat/completions"

# Find English recipes
for i, r in enumerate(recipes):
    instr = r.get("instructions", "")
    if not instr or instr[:3] not in ['Add','Pre','Pla','Hea','Pou','Mix','Bri','Coo','Sti','In ']:
        continue
    
    prompt = f"""Translate this recipe to Swedish. Keep the same format.
Title: {r['title']}
Instructions: {instr[:800]}

Return ONLY:
TITEL: [translated title]
INSTRUKTIONER: [translated instructions]"""

    try:
        data = json.dumps({
            "model": "deepseek-chat", "messages": [{"role":"user","content":prompt}],
            "max_tokens": 500, "temperature": 0.3
        }).encode()
        req = urllib.request.Request(DS_URL, data=data, headers={
            "Content-Type":"application/json", "Authorization":f"Bearer {DK}"
        })
        resp = urllib.request.urlopen(req, timeout=20)
        text = json.loads(resp.read())["choices"][0]["message"]["content"]
        
        for line in text.split('\n'):
            if line.startswith("TITEL:"):
                r["title"] = line[6:].strip()
            elif line.startswith("INSTRUKTIONER:"):
                r["instructions"] = line[15:].strip() + "\n" + "\n".join(
                    l for l in text.split('\n')[text.split('\n').index(line)+1:] if l.strip()
                )
        
        if i % 20 == 0:
            with open("recipes.json","w") as f:
                json.dump(recipes, f, ensure_ascii=False, indent=2)
            en = sum(1 for r2 in recipes if r2.get('instructions','')[:3] in ['Add','Pre','Pla'])
            print(f"  {i}: translated, {en} kvar")
        time.sleep(1)
    except Exception as e:
        print(f"  ✗ {r['title'][:30]}: {e}")
        time.sleep(2)

with open("recipes.json","w") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)
en = sum(1 for r in recipes if r.get('instructions','')[:3] in ['Add','Pre','Pla'])
print(f"\n✅ Done! {en} English recipes remaining")
