#!/usr/bin/env python3
"""Generate healthy Swedish recipes"""
import json, os, time, urllib.request, sys

sys.stdout.reconfigure(line_buffering=True)

with open("recipes.json") as f:
    recipes = json.load(f)

env_path = os.path.expanduser("~/.hermes/.env")
DK = ""
with open(env_path) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY"):
            DK = line.split("=",1)[1].strip()

existing_titles = {r["title"].lower() for r in recipes}
new_id = 90000
DS_URL = "https://api.deepseek.com/chat/completions"
BATCH = 10
new_recipes = []
total_needed = 334  # to reach 1000 total

cats = ["Sallad","Soppa","Grillad fisk","Wok","Vegansk","Vegetarisk","Medelhavskost","Kycklingrätter","Proteinrik","Lågkalori","Glutenfri","Smoothie Bowl","Skaldjur","Meal Prep","Frukost"]
target_per_cat = max(1, total_needed // len(cats))

with open("gen_log.txt", "w") as log:
    for cat in cats:
        log.write(f"\n📁 {cat}: generating {target_per_cat}...\n")
        log.flush()
        generated = 0
        while generated < target_per_cat:
            prompt = f"""Generate {BATCH} unique healthy Swedish recipes for category "{cat}".
Return ONLY a valid JSON array. Each recipe: id, title (Swedish), category, area:"Swedish", instructions (Swedish, detailed), tags:"nyttig,hälsosam", ingredients:[...], measures:[...]
Be creative and varied."""
            
            try:
                data = json.dumps({
                    "model": "deepseek-chat", "messages": [{"role":"user","content":prompt}],
                    "max_tokens": 2500, "temperature": 0.95
                }).encode()
                req = urllib.request.Request(DS_URL, data=data, headers={
                    "Content-Type": "application/json", "Authorization": f"Bearer {DK}"
                })
                resp = urllib.request.urlopen(req, timeout=45)
                result = json.loads(resp.read())["choices"][0]["message"]["content"]
                
                result = result.strip()
                if "```" in result:
                    result = result.split("```")[1]
                    if result.startswith("json"): result = result[4:]
                
                # Fix common JSON issues from LLM output
                import re
                # Remove trailing commas before ] or }
                result = re.sub(r',\s*([}\]])', r'\1', result)
                # Fix unescaped newlines inside strings 
                result = re.sub(r'(?<=[^\\])\\(?=[^"\\nrtbf/])', r'\\\\', result)
                
                try:
                    batch = json.loads(result)
                except:
                    # Try to extract array manually
                    start = result.find('[')
                    end = result.rfind(']') + 1
                    if start >= 0 and end > start:
                        try:
                            batch = json.loads(result[start:end])
                        except:
                            raise Exception(f"JSON parse failed: {result[:100]}")
                    else:
                        raise Exception(f"No JSON array: {result[:100]}")
                if isinstance(batch, dict): batch = [batch]
                
                added = 0
                for r in batch:
                    t = r.get("title","").lower()
                    if t and t not in existing_titles:
                        r["id"] = str(new_id); r["thumb"] = ""; r["youtube"] = ""
                        new_recipes.append(r); existing_titles.add(t); new_id += 1; added += 1
                
                generated += added
                recipes.extend(new_recipes[-added:])
                with open("recipes.json","w") as f: json.dump(recipes, f, ensure_ascii=False, indent=2)
                
                msg = f"  +{added} (total AI:{len(new_recipes)}, all:{len(recipes)})"
                log.write(msg + "\n"); log.flush(); print(msg)
                time.sleep(1.5)
            except Exception as e:
                log.write(f"  ✗ {e}\n"); log.flush(); print(f"  ✗ {e}")
                time.sleep(3)

print(f"\n✅ Done! {len(new_recipes)} new, {len(recipes)} total")
