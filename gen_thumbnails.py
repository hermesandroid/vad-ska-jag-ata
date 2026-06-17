#!/usr/bin/env python3
"""Generate placeholder food images for recipes without photos."""
import json, os, hashlib, base64

with open("recipes.json") as f:
    recipes = json.load(f)

needs_photo = [r for r in recipes if not r.get('thumb', '') or not r['thumb'].startswith('http')]
print(f"Recipes needing photos: {len(needs_photo)}")

# Category → emoji + color mapping
CAT_STYLE = {
    "Soppa": ("🥣", "#f97316,#ea580c"),
    "Vegansk": ("🥬", "#22c55e,#15803d"),
    "Vegetarisk": ("🥗", "#84cc16,#4d7c0f"),
    "Fisk": ("🐟", "#06b6d4,#0891b2"),
    "Kyckling": ("🍗", "#f59e0b,#d97706"),
    "Kött": ("🥩", "#ef4444,#b91c1c"),
    "Dessert": ("🍰", "#ec4899,#be185d"),
    "Bakverk": ("🧁", "#f472b6,#db2777"),
    "Sallad": ("🥗", "#10b981,#047857"),
    "Pasta": ("🍝", "#eab308,#ca8a04"),
    "Frukost": ("🍳", "#fb923c,#ea580c"),
    "Svensk": ("🇸🇪", "#3b82f6,#1d4ed8"),
    "Snacks": ("🍿", "#a855f7,#7c3aed"),
}

def get_style(recipe):
    cat = recipe.get('category', '')
    area = recipe.get('area', '')
    for key, style in CAT_STYLE.items():
        if key.lower() in cat.lower() or key.lower() in area.lower():
            return style
    # Default based on hash for variety
    colors = [
        ("🍽️", "#6366f1,#4f46e5"),
        ("🍳", "#f59e0b,#d97706"),
        ("🥘", "#ef4444,#dc2626"),
        ("🍲", "#10b981,#059669"),
        ("🧆", "#8b5cf6,#6d28d9"),
    ]
    h = int(hashlib.md5(recipe['title'].encode()).hexdigest()[:8], 16)
    return colors[h % len(colors)]

# Create SVG placeholder as data URI
os.makedirs("thumbnails", exist_ok=True)

generated = 0
for r in needs_photo:
    emoji, gradient = get_style(r)
    title = r['title'][:30]
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:{gradient.split(',')[0]}"/>
    <stop offset="100%" style="stop-color:{gradient.split(',')[1]}"/>
  </linearGradient></defs>
  <rect width="400" height="300" fill="url(#g)"/>
  <text x="200" y="120" text-anchor="middle" font-size="64">{emoji}</text>
  <text x="200" y="180" text-anchor="middle" font-size="20" fill="white" font-family="system-ui,sans-serif" font-weight="bold">{title}</text>
  <text x="200" y="210" text-anchor="middle" font-size="14" fill="rgba(255,255,255,0.8)" font-family="system-ui,sans-serif">{r.get('category','')} · {r.get('area','')}</text>
</svg>'''
    
    # Save SVG
    fname = f"thumb_{r['id']}.svg"
    with open(f"thumbnails/{fname}", "w") as f:
        f.write(svg)
    
    # Set thumb to the SVG file
    r['thumb'] = f"thumbnails/{fname}"
    generated += 1

# Save updated recipes
with open("recipes.json", "w") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)

print(f"Generated {generated} placeholder images → thumbnails/")
