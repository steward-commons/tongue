# Tongue

A small, playful taste simulator. Give it a recipe as JSON (ingredient names and grams) and it estimates how the dish tastes on 0–10 scales: sweet, salty, sour, bitter, umami, chili heat, fat, aroma, and temperature.

It cannot actually taste anything. It scores a recipe from an ingredient table of hand-made estimates, so treat the numbers as a conversation starter, then calibrate against what a real person says.

## Features

- **Chili heat** from real Scoville ranges, diluted by dish weight and put on a log scale. A second "spice-lover" reading is shown about 2.5 points lower.
- **Temperature** as its own scale (frozen, cold, cool, room, hot, scorching), separate from chili heat.
- **Drinks**: water, ice, and carbonated water are solvents, so flavor comes from concentration (g per 100 ml), not mass share. Fizz is its own sensation.
- **Dilution**: ice melt and a fizzy drink going flat over time.
- **Layers**: an optional time sequence (coating, then core), so a sour blast is not averaged away.
- **Dunk**: dunk a cookie in milk (quick and long dips): softer, cooler, creamier, a touch less sweet.

## Usage

```bash
python3 tongue.py examples/bibimbap.json
python3 tongue.py examples/dr-pepper.json dilute cold
python3 tongue.py examples/warheads.json layers
python3 tongue.py examples/chocolate-chip-cookie.json dunk room "chocolate milk"
```

Arguments: `food.json [all|each|layers|dilute|dunk] [frozen|cold|room|hot|scorching] [dunk liquid]`.

## Recipe format

```json
{"name": "My dish", "carbonation": 0,
 "ingredients": [{"name": "rice", "grams": 250}, {"name": "gochujang", "grams": 25}]}
```

Ingredient names must exist in `ingredients.json`. Add your own entries there; every value is an estimate.

## Tests

```bash
python3 -m unittest discover -s tests
```

## License

MIT. See `LICENSE`.
