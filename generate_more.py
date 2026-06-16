#!/usr/bin/env python3
"""Generate 4000+ healthy recipes via DeepSeek"""
import json, os, time, urllib.request

with open("recipes.json") as f:
    existing = json.load(f)

env_path = os.path.expanduser("~/.hermes/.env")
DK = ""
with open(env_path) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY"):
            DK = line.split("=",1)[1].strip()

existing_titles = {r["title"].lower() for r in existing}
new_id = 90000

# Healthy categories to generate
categories = [
    ("Sallad", 300), ("Soppa", 250), ("Grillad fisk", 200), 
    ("Wok & Stir Fry", 250), ("Vegansk", 300), ("Vegetarisk", 350),
    ("Medelhavskost", 250), ("Kycklingrätter", 250), ("Slow Cooker", 200),
    ("Proteinrik", 200), ("Lågkalori", 200), ("Glutenfri", 200),
    ("Raw food", 150), ("Smoothies & Bowls", 200), ("Skaldjur", 200),
    ("Asiatiskt nyttigt", 200), ("Mexikanskt nyttigt", 150), ("Meal Prep", 200),
    ("Frukost", 150), ("Mellanmål", 150)
]

DS_URL = "https://api.deepseek.com/chat/completions"
new_recipes = []
BATCH = 20  # Generate 20 recipes per API call for speed

for cat, target in categories:
    print(f"\n📁 {cat}: generating {target} healthy recipes...")
    generated = 0
    while generated < target:
        batch_size = min(BATCH, target - generated)
        prompt = f"""Generate {batch_size} unique healthy Swedish-friendly recipes for category "{cat}".

Return ONLY a valid JSON array, no other text. Each recipe:
- Use Swedish or international names
- Focus on HEALTH: low calorie, high nutrients, whole foods, no processed ingredients
- Include realistic Swedish-available ingredients
- Write instructions in Swedish
- Add health tags like: nyttig, lågkalori, proteinrik, vegansk, vegetarisk, glutenfri, etc.

Format:
[
  {{
    "id": "90001",
    "title": "Recipe name",
    "category": "{cat}",
    "area": "Swedish",
    "instructions": "Step by step in Swedish...",
    "tags": "nyttig,lågkalori,proteinrik",
    "ingredients": ["ingredient1", "ingredient2"],
    "measures": ["2 dl", "1 st"]
  }}
]

Make every recipe genuinely different. Be creative!"""

        try:
            data = json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.95
            }).encode()
            req = urllib.request.Request(DS_URL, data=data, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DK}"
            })
            resp = urllib.request.urlopen(req, timeout=45)
            result = json.loads(resp.read())["choices"][0]["message"]["content"]
            
            # Extract JSON array
            result = result.strip()
            if "```" in result:
                result = result.split("```")[1]
                if result.startswith("json"): result = result[4:]
            
            batch = json.loads(result)
            if isinstance(batch, dict): batch = [batch]  # Single recipe
            
            added = 0
            for recipe in batch:
                title = recipe.get("title", "").lower()
                if title and title not in existing_titles:
                    recipe["id"] = str(new_id)
                    recipe["thumb"] = ""
                    recipe["youtube"] = ""
                    new_recipes.append(recipe)
                    existing_titles.add(title)
                    new_id += 1
                    added += 1
            
            generated += added
            print(f"  +{added} recipes (total: {len(new_recipes)})", end="\r")
            time.sleep(2)
            
        except Exception as e:
            print(f"\n  ✗ Error: {e}")
            time.sleep(3)

print(f"\n\n✅ Generated {len(new_recipes)} healthy recipes!")

all_recipes = existing + new_recipes
with open("recipes.json", "w", encoding="utf-8") as f:
    json.dump(all_recipes, f, ensure_ascii=False, indent=2)
print(f"Total: {len(all_recipes)} recipes in recipes.json")
