#!/usr/bin/env python3
"""Simple one-at-a-time recipe generation"""
import json, os, time, urllib.request

with open("recipes.json") as f: recipes = json.load(f)
existing_titles = {r["title"].lower() for r in recipes}

env_path = os.path.expanduser("~/.hermes/.env")
with open(env_path) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY"):
            DK = line.split("=",1)[1].strip()

DS_URL = "https://api.deepseek.com/chat/completions"
cats = ["Sallad","Soppa","Grillad fisk","Wok","Vegansk","Vegetarisk","Medelhavskost",
        "Kycklingrätter","Proteinrik","Lågkalori","Glutenfri","Smoothie Bowl","Skaldjur","Meal Prep"]
new_id = 99000
added = 0
TARGET = 200  # quick batch to prove it works

for i in range(TARGET):
    cat = cats[i % len(cats)]
    prompt = f"""Skapa ett nytt, unikt hälsosamt svenskt recept i kategorin "{cat}".

Returnera ENDAST denna exakta text, inget annat:
TITEL: [kreativt svenskt namn]
KATEGORI: {cat}
TID: [X min]
SVÅRIGHET: [lätt/medel/svår]
TAGS: nyttig,hälsosam,[valfria]

INGREDIENSER:
- [mängd] [ingrediens]
- [mängd] [ingrediens]
(4-8 ingredienser)

INSTRUKTIONER:
1. [steg]
2. [steg]
(3-6 steg på svenska)"""

    try:
        data = json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.95
        }).encode()
        req = urllib.request.Request(DS_URL, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DK}"
        })
        resp = urllib.request.urlopen(req, timeout=20)
        text = json.loads(resp.read())["choices"][0]["message"]["content"]
        
        # Parse the simple format
        lines = text.strip().split('\n')
        title = cat_time = diff = ""
        tags = ""
        ingredients = []; measures = []
        instructions = ""
        in_ingr = in_instr = False
        
        for line in lines:
            line = line.strip()
            if line.startswith("TITEL:"): title = line[6:].strip()
            elif line.startswith("TID:"): cat_time = line[4:].strip()
            elif line.startswith("SVÅRIGHET:"): diff = line[10:].strip()
            elif line.startswith("TAGS:"): tags = line[5:].strip()
            elif line.startswith("INGREDIENSER:"): in_ingr = True; in_instr = False
            elif line.startswith("INSTRUKTIONER:"): in_ingr = False; in_instr = True
            elif in_ingr and line.startswith("- "):
                parts = line[2:].split(" ", 1)
                if len(parts) == 2:
                    measures.append(parts[0]); ingredients.append(parts[1])
            elif in_instr:
                instructions += line + "\n"
        
        if title and title.lower() not in existing_titles:
            existing_titles.add(title.lower())
            recipes.append({
                "id": str(new_id), "title": title, "category": cat,
                "area": "Swedish", "instructions": instructions.strip(),
                "thumb": "", "youtube": "", "tags": tags,
                "ingredients": ingredients, "measures": measures
            })
            new_id += 1; added += 1
            
            # Save every 10
            if added % 10 == 0:
                with open("recipes.json", "w") as f:
                    json.dump(recipes, f, ensure_ascii=False, indent=2)
                print(f"  Saved {len(recipes)} recipes (+{added})")
        
        time.sleep(1.2)
    except Exception as e:
        print(f"  ✗ {e}")
        time.sleep(2)

# Final save
with open("recipes.json", "w") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)
print(f"\n✅ Added {added} recipes! Total: {len(recipes)}")
