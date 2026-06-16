#!/usr/bin/env python3
"""Translate all existing English recipes to Swedish"""
import json, os, time, urllib.request

with open("recipes.json") as f:
    recipes = json.load(f)

env_path = os.path.expanduser("~/.hermes/.env")
DK = ""
with open(env_path) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY"):
            DK = line.split("=",1)[1].strip()

DS_URL = "https://api.deepseek.com/chat/completions"

# Find recipes with English instructions
to_translate = [r for r in recipes if r.get("instructions","") and any(w in r["instructions"][:30] for w in ["Add ","Preheat","Place","Heat ","Pour ","Mix ","Bring","Cook ","Stir ","In a"])]
print(f"Found {len(to_translate)} English recipes to translate")

translated = 0
BATCH = 15

for i in range(0, len(to_translate), BATCH):
    batch = to_translate[i:i+BATCH]
    recipes_json = json.dumps(batch, ensure_ascii=False)
    
    prompt = f"""Translate these recipes to Swedish. Return the SAME JSON array, but translate:
- title → Swedish
- instructions → Swedish  
- Keep ingredients in original language but translate measures if needed
- Keep category, area, tags as-is

Recipes:
{recipes_json}

Return ONLY the JSON array, no other text."""

    try:
        data = json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.3
        }).encode()
        req = urllib.request.Request(DS_URL, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DK}"
        })
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())["choices"][0]["message"]["content"]
        
        # Extract JSON
        result = result.strip()
        if "```" in result:
            part = result.split("```")[1]
            if part.startswith("json"): part = part[4:]
            translated_batch = json.loads(part)
        else:
            translated_batch = json.loads(result)
        
        if isinstance(translated_batch, dict): translated_batch = [translated_batch]
        
        # Update recipes
        for tr in translated_batch:
            for orig in recipes:
                if orig["id"] == tr["id"]:
                    orig["title"] = tr.get("title", orig["title"])
                    orig["instructions"] = tr.get("instructions", orig["instructions"])
                    break
        
        translated += len(batch)
        print(f"  Translated {translated}/{len(to_translate)}", end="\r")
        time.sleep(2)
        
    except Exception as e:
        print(f"\n  ✗ Batch {i}: {e}")
        time.sleep(3)

# Save
with open("recipes.json", "w", encoding="utf-8") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)
print(f"\n✅ Done! {len(recipes)} recipes saved")
