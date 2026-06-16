#!/usr/bin/env python3
"""Fetch all recipes from TheMealDB and save as JSON"""
import json, time, urllib.request

BASE = "https://www.themealdb.com/api/json/v1/1/search.php?f="
all_meals = []

for letter in "abcdefghijklmnopqrstuvwxyz":
    url = BASE + letter
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        meals = data.get("meals") or []
        for m in meals:
            all_meals.append({
                "id": m["idMeal"],
                "title": m["strMeal"],
                "category": m.get("strCategory", ""),
                "area": m.get("strArea", ""),
                "instructions": m.get("strInstructions", ""),
                "thumb": m.get("strMealThumb", ""),
                "tags": m.get("strTags", ""),
                "youtube": m.get("strYoutube", ""),
                "ingredients": [
                    m.get(f"strIngredient{i}") 
                    for i in range(1, 21) 
                    if m.get(f"strIngredient{i}")
                ],
                "measures": [
                    m.get(f"strMeasure{i}") 
                    for i in range(1, 21) 
                    if m.get(f"strMeasure{i}")
                ]
            })
        print(f"  {letter}: {len(meals)} meals (total: {len(all_meals)})")
        time.sleep(0.3)
    except Exception as e:
        print(f"  {letter}: ERROR {e}")

with open("../recipes.json", "w", encoding="utf-8") as f:
    json.dump(all_meals, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved {len(all_meals)} recipes to recipes.json")
