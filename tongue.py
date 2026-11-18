#!/usr/bin/env python3
"""A simulated tongue (v0.5).
- Scales are 0-10. Ingredient values are my estimates, calibrated against one taster's feedback.
- Heat: capsaicin from real SHU ranges (shu field, midpoint), diluted by dish
  weight and put on a log scale. Non-capsaicin bite (garlic, pepper) stays as 'bite'.
  A spice lover's scale is about 2.5 lower than the baseline; both are shown.
- Temperature: warm food reads more aromatic and a bit sweeter; cold food is duller
  and greasier. For water-based drinks, cold does not knock down sweetness (sugar in
  solution stays sweet; iced drinks often seem to start sweeter). Dilution handles the fade.
- Drinks: water, ice, and carbonated water are solvents. Flavor comes from
  concentration (g per 100 ml of the finished drink), not mass share.
- Carbonation is its own sensation (fizz / tingle / bite).
- Mode 'each' tastes components one at a time; 'all' tastes them as one bite;
  'layers' is an optional time sequence (coating, then core); 'dilute' shows ice
  melt and/or a drink going flat.
Usage: tongue.py food.json [all|each|layers|dilute|dunk] [frozen|cold|room|hot|scorching] [dunk liquid]
- v0.3: 'temp' is its own scale (physical heat, separate from chili heat); basic tastes plateau.
- v0.4: drink concentration, fizz, dilution over time, optional layers, a spice-lover heat scale.
- v0.5 (2026-11-18): 'dunk' mode for cookies. The dunked bite soaks up liquid
  (my estimates: quick 1-2 s dip ~30% of the dunked half's weight, long 4-5 s ~60%),
  is tasted as one bite at a new 'cool' temp (fridge milk chills it, no extra cold-fat bump), and gets a texture note.
  Default liquid is whole milk; pass 'chocolate milk' as the 4th arg to switch."""
import json, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
SCALES = ["sweet","salty","sour","bitter","umami","heat","fat","aroma","temp"]
ING = json.load(open(os.path.join(HERE, "ingredients.json")))
MAX_SHU_EFF = 100000  # dish-level effective SHU that maxes the scale
REF_CONC = 10.0       # g/100ml at which a bulk solute (e.g. sugar) has weight 1
SPICE_LOVER_HEAT = 2.5
SOLVENTS = ("water", "carbonated water")
WATER_FRAC = 0.5

def plateau(v):
    return v if v <= 7 else 7 + 3*(1-math.exp(-(v-7)/3))

def apply_temp(prof, temp, drink=False):
    prof["temp"] = {"frozen":0,"cold":2,"cool":3,"room":4,"hot":7,"scorching":10}.get(temp,4)
    if temp == "cool":  # v0.5: room food touched by cold liquid (a dunk); milk brings its own fat
        prof["aroma"]*=0.85
        if not drink:
            prof["sweet"]*=0.95
    if temp in ("hot","scorching"):
        prof["aroma"]*=1.2; prof["sweet"]*=1.1; prof["fat"]*=0.9
    if temp in ("cold","frozen"):
        prof["aroma"]*=0.7
        if not drink:
            prof["sweet"]*=0.85
        prof["fat"]*=1.15
    return prof

def finish_profile(out, shu, temp, drink=False, fizz=0.0):
    prof = {s: min(10, v*0.85) for s,v in out.items()}
    for s in ["sweet","salty","sour","bitter","umami"]:
        prof[s] = plateau(prof[s])
    prof = apply_temp(prof, temp, drink=drink)
    cap = 10*math.log10(1+shu)/math.log10(1+MAX_SHU_EFF)
    prof["heat"] = min(10, max(cap, prof.get("heat",0)))
    if fizz > 0:
        prof["fizz"] = min(10, fizz)
    return {s: round(min(10,v),1) for s,v in prof.items()}

def taste_solid(recipe, temp="room"):
    total = sum(g for _, g in recipe)
    out = {s: 0.0 for s in SCALES}; missing = []; shu = 0.0
    for name, g in recipe:
        p = ING.get(name)
        if p is None:
            missing.append(name); continue
        w = math.sqrt(g/total) if total else 0
        for s in SCALES:
            if s != "heat": out[s] += p.get(s,0)*w
        out["heat"] += p.get("bite",0)*w*0.3
        shu += p.get("shu",0)*g/total if total else 0
    return finish_profile(out, shu, temp, drink=False), round(shu), missing

def water_based(recipe):
    total = sum(g for _, g in recipe)
    sol = sum(g for n, g in recipe if n in SOLVENTS)
    return total > 0 and sol/total >= WATER_FRAC

def liquid_recipe(recipe, melt_frac=0.0):
    liquid, melted = [], 0.0
    for n, g in recipe:
        if n == "ice":
            melted += g * melt_frac
        else:
            liquid.append((n, g))
    if melted:
        liquid.append(("water", melted))
    return liquid

def taste_drink(recipe, temp="room", carbonation=0, flat_frac=0.0):
    finished_ml = sum(g for _, g in recipe) or 1  # 1 g ≈ 1 ml
    out = {s: 0.0 for s in SCALES}; missing = []; shu = 0.0
    for name, g in recipe:
        if name in SOLVENTS:
            continue
        p = ING.get(name)
        if p is None:
            missing.append(name); continue
        ref = p.get("ref_conc", REF_CONC)
        c = g / finished_ml * 100.0
        w = math.sqrt(max(c, 0)/ref) if ref else 0
        for s in SCALES:
            if s != "heat": out[s] += p.get(s,0)*w
        out["heat"] += p.get("bite",0)*w*0.3
        shu += p.get("shu",0)*g/finished_ml
    fizz = carbonation
    if fizz <= 0:
        for n, _ in recipe:
            if n == "carbonated water":
                fizz = max(fizz, ING.get(n, {}).get("fizz", 8))
    fizz = max(0.0, fizz * (1 - 0.7*flat_frac))
    out["sour"] += fizz * 0.12  # carbonic tang
    prof = finish_profile(out, shu, temp, drink=True, fizz=fizz)
    return prof, round(shu), missing

def taste(recipe, temp="room", melt_frac=0.0, carbonation=0, flat_frac=0.0):
    liquid = liquid_recipe(recipe, melt_frac)
    if water_based(liquid):
        return taste_drink(liquid, temp, carbonation, flat_frac)
    return taste_solid(liquid, temp)

def bar(v):
    n=int(round(v)); return "#"*n + "."*(10-n)

def show(title, recipe, temp, carbonation=0, melt_frac=0.0, flat_frac=0.0):
    prof, shu, missing = taste(recipe, temp, melt_frac, carbonation, flat_frac)
    print(f"{title}  [{temp}, ~{shu} effective SHU]")
    for s in SCALES:
        print(f"  {s:7s} {bar(prof[s])} {prof[s]}")
        if s == "heat" and prof[s] > 0:
            print(f"          (spice-lover scale: {round(max(0.0, prof[s]-SPICE_LOVER_HEAT),1)})")
    if prof.get("fizz", 0) > 0:
        print(f"  {'fizz':7s} {bar(prof['fizz'])} {prof['fizz']}")
    if missing:
        print("  unknown:", ", ".join(missing))
    return prof

if __name__ == "__main__":
    food = json.load(open(sys.argv[1]))
    mode = sys.argv[2] if len(sys.argv)>2 else "all"
    temp = sys.argv[3] if len(sys.argv)>3 else "room"
    temps = food.get("temps", {})
    carb = food.get("carbonation", 0)
    items = [(i["name"], i["grams"]) for i in food["ingredients"]]
    if mode == "each":
        for n,g in items:
            show(f"{n} ({g} g)", [(n,g)], temps.get(n, temp), carb)
    elif mode == "layers":
        layers = food.get("layers")
        if not layers:
            print("No layers defined for this food; falling back to all-at-once.")
            show(food["name"], items, temp, carb)
        else:
            print(f"{food['name']}  [layers]")
            for layer in layers:
                li = [(i["name"], i["grams"]) for i in layer["ingredients"]]
                show(layer["name"], li, layer.get("temp", temp), layer.get("carbonation", carb))
    elif mode == "dilute":
        has_ice = any(n=="ice" for n,_ in items)
        has_fizz = bool(carb) or any(n=="carbonated water" for n,_ in items)
        if not has_ice and not has_fizz:
            show(food["name"], items, temp, carb)
        else:
            steps = [
                ("just poured / opened", 0.0, 0.0),
                ("ice half-melted" if has_ice else "after sitting a while",
                 0.5 if has_ice else 0.0, 0.35 if has_fizz else 0.0),
                ("watered down / going flat" if (has_ice and has_fizz)
                 else ("mostly melted, watered down" if has_ice else "going flat"),
                 1.0 if has_ice else 0.0, 0.75 if has_fizz else 0.0),
            ]
            for title, melt, flat in steps:
                show(f"{food['name']} — {title}", items, temp, carb, melt, flat)
    elif mode == "dunk":
        liquid = sys.argv[4] if len(sys.argv)>4 else food.get("dunk_liquid", "whole milk")
        total = sum(g for _,g in items)
        half = [(n, g/2) for n,g in items]  # the dunked half of the cookie
        print(f"{food['name']}  [dunked in {liquid}]")
        show("dry bite (no dunk)", items, temp, carb)
        print("  texture: crisp edge, chewy center, firm chips")
        for title, soak, tex in [
            ("quick dunk (1-2 s)", 0.3, "edge softened, center still chewy, chips cool and firm; milk coats the tongue"),
            ("long dunk (4-5 s)", 0.6, "soft all the way through, nearly melts, risk of the drop-off; chips smear"),
        ]:
            bite = half + [(liquid, round(total/2*soak,1))]
            show(f"{title} (+{round(total/2*soak,1)} g {liquid} in the dunked half)", bite, "cool", carb)
            print(f"  texture: {tex}")
    else:
        show(food["name"], items, temp, carb)
