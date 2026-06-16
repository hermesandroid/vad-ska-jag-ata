#!/usr/bin/env python3
"""Fetch recipes by ingredient from TheMealDB, deduplicate, merge"""
import json, time, urllib.request, os

# Load existing
with open("recipes.json") as f:
    existing = json.load(f)

existing_ids = {r["id"] for r in existing}

# Get all ingredients
print("Fetching ingredients...")
req = urllib.request.Request("https://www.themealdb.com/api/json/v1/1/list.php?i=list",
                             headers={"User-Agent": "Mozilla/5.0"})
data = json.loads(urllib.request.urlopen(req, timeout=15).read())
ingredients = [m["strIngredient"] for m in data.get("meals", [])]
print(f"Found {len(ingredients)} ingredients")

BASE = "https://www.themealdb.com/api/json/v1/1/"
new_recipes = []

for i, ing in enumerate(ingredients):
    if i % 50 == 0:
        print(f"  Progress: {i}/{len(ingredients)} ({len(new_recipes)} new recipes)")
    
    try:
        q = urllib.parse.quote(ing.replace(" ", "_"))
        url = f"{BASE}filter.php?i={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        meals = data.get("meals") or []
        
        for m in meals:
            mid = m["idMeal"]
            if mid not in existing_ids:
                existing_ids.add(mid)
                # Fetch full details
                time.sleep(0.15)
                try:
                    req2 = urllib.request.Request(f"{BASE}lookup.php?i={mid}",
                                                  headers={"User-Agent": "Mozilla/5.0"})
                    detail = json.loads(urllib.request.urlopen(req2, timeout=10).read())
                    fm = (detail.get("meals") or [None])[0]
                    if fm:
                        new_recipes.append({
                            "id": fm["idMeal"],
                            "title": fm["strMeal"],
                            "category": fm.get("strCategory", ""),
                            "area": fm.get("strArea", ""),
                            "instructions": fm.get("strInstructions", ""),
                            "thumb": fm.get("strMealThumb", ""),
                            "tags": fm.get("strTags", ""),
                            "youtube": fm.get("strYoutube", ""),
                            "ingredients": [fm.get(f"strIngredient{j}") for j in range(1,21) if fm.get(f"strIngredient{j}")],
                            "measures": [fm.get(f"strMeasure{j}") for j in range(1,21) if fm.get(f"strMeasure{j}")]
                        })
                except:
                    pass
        time.sleep(0.1)
    except Exception as e:
        if i % 100 == 0:
            print(f"  Error on {ing}: {e}")

print(f"\n✅ Fetched {len(new_recipes)} new recipes!")

# Merge
all_recipes = existing + new_recipes
with open("recipes.json", "w", encoding="utf-8") as f:
    json.dump(all_recipes, f, ensure_ascii=False, indent=2)
print(f"Total: {len(all_recipes)} recipes")
