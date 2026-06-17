#!/usr/bin/env python3
"""Extract structured ingredients from AI recipe instructions using DeepSeek."""
import json, os, time, urllib.request

with open("recipes.json") as f:
    recipes = json.load(f)

env_path = os.path.expanduser("~/.hermes/.env")
with open(env_path) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY"):
            DK = line.split("=", 1)[1].strip()

DS_URL = "https://api.deepseek.com/chat/completions"

# Find recipes needing ingredients
needy = [(i, r) for i, r in enumerate(recipes)
         if not r.get('ingredients') or not isinstance(r.get('ingredients'), list)
         or len(r.get('ingredients', []) if isinstance(r.get('ingredients'), list) else []) == 0]

print(f"Found {len(needy)} recipes needing ingredients")

BATCH = 10
total_cost = 0

for batch_start in range(0, len(needy), BATCH):
    batch = needy[batch_start:batch_start + BATCH]
    
    # Build prompt with all recipes in this batch
    parts = []
    for _, r in batch:
        parts.append(f"[ID:{r['id']}] {r['title']}\nInstructions: {r['instructions'][:600]}")
    
    prompt = f"""Extract a structured ingredients list from each recipe below.
For each recipe, output ONLY a JSON array of objects with "ingredients" (list of strings) and "measures" (list of strings, one per ingredient).
Format: {{"ID": [["ingredient1","measure1"],["ingredient2","measure2"],...], "ID2": [...], ...}}

Recipes:
{chr(10).join(parts)}

Return ONLY valid JSON, no other text."""

    try:
        data = json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000, "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }).encode()
        
        req = urllib.request.Request(DS_URL, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + DK
        })
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        extracted = json.loads(content)
        
        # Calculate token usage
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost = (prompt_tokens * 0.15 + completion_tokens * 0.60) / 1_000_000  # Pro rates
        total_cost += cost
        
        # Update recipes
        updated = 0
        for idx, r in batch:
            rid = r['id']
            if rid in extracted:
                ings_meas = extracted[rid]
                ings = [item[0] for item in ings_meas]
                meas = [item[1] if len(item) > 1 else "" for item in ings_meas]
                r['ingredients'] = ings
                r['measures'] = meas
                updated += 1
        
        done = batch_start + len(batch)
        print(f"  Batch {batch_start//BATCH+1}: {updated}/{len(batch)} updated | "
              f"tokens: {prompt_tokens}+{completion_tokens} | "
              f"cost: ${cost:.4f} | total: ${total_cost:.4f}")
        
        # Save progress
        with open("recipes.json", "w") as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2)
        
        if done < len(needy):
            time.sleep(1)
            
    except Exception as e:
        print(f"  ✗ Batch {batch_start//BATCH+1}: {e}")
        time.sleep(2)

# Count remaining
remaining = sum(1 for r in recipes if not r.get('ingredients') or len(r.get('ingredients', []) if isinstance(r.get('ingredients'), list) else []) == 0)
print(f"\nDone! ${total_cost:.4f} total. {len(needy) - remaining} recipes updated, {remaining} still need ingredients")
