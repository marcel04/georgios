"""Canonical Georgio's menu seed data.

Source:
    https://www.georgiosroastbeefandpizza.com/menu.html

Snapshot:
    September 2026

Conventions:
- Fixed prices are stored as strings so the seed loader can convert them directly
  to Decimal without passing through binary floating-point values.
- Items with one fixed price use a single ``Regular`` variant unless the published
  menu gives a more specific size/name.
- ``MENU_DATA`` contains only entries that can be represented safely by the
  current fixed-price schema.
- Market-price and source-format ambiguities are listed in ``SEED_REVIEW_NOTES``
  rather than given invented values.
- Modifier-like offerings (pizza toppings, salad toppers, gluten-free upgrades,
  sauces, etc.) are intentionally not flattened into ordinary menu items here;
  they should be represented through GEO-20 modifier tables when seeded.
"""


def _regular(price: str) -> list[dict[str, object]]:
    return [{"name": "Regular", "price": price, "display_order": 1}]


def _sizes(*pairs: tuple[str, str]) -> list[dict[str, object]]:
    return [
        {"name": name, "price": price, "display_order": index}
        for index, (name, price) in enumerate(pairs, start=1)
    ]


MENU_DATA = [
    {
        "name": "Georgio's Famous Hot Roast Beef",
        "display_order": 1,
        "items": [
            {
                "name": "Super Beef",
                "description": "Served on a grilled onion roll",
                "display_order": 1,
                "variants": _regular("11.25"),
            },
            {
                "name": "Regular Beef",
                "description": "Served on a grilled seeded roll",
                "display_order": 2,
                "variants": _regular("10.15"),
            },
            {
                "name": "Junior Beef",
                "description": "Served on a grilled plain roll",
                "display_order": 3,
                "variants": _regular("8.95"),
            },
            {
                "name": "Large Beef Sub",
                "description": "Served on a grilled sub roll",
                "display_order": 4,
                "variants": _regular("14.95"),
            },
            {
                "name": "Small Beef Sub",
                "description": "Served on a grilled sub roll",
                "display_order": 5,
                "variants": _regular("12.60"),
            },
        ],
    },
    {
        "name": "Hot Sandwiches",
        "display_order": 2,
        "items": [
            {
                "name": "Super Pastrami",
                "description": "Served on grilled onion roll",
                "display_order": 1,
                "variants": _regular("13.75"),
            },
            {
                "name": "Regular Pastrami",
                "description": "Served on grilled seeded roll",
                "display_order": 2,
                "variants": _regular("11.75"),
            },
            {
                "name": "1/2 lb. Homemade Hamburger",
                "display_order": 3,
                "variants": _regular("6.05"),
            },
            {
                "name": "1/2 lb. Homemade Cheeseburger",
                "display_order": 4,
                "variants": _regular("8.05"),
            },
            {
                "name": "Haddock Sandwich",
                "display_order": 5,
                "variants": _regular("12.05"),
            },
            {"name": "King Hot Dog", "display_order": 6, "variants": _regular("4.45")},
            {
                "name": "Gyro",
                "description": "Grilled strips of seasoned beef, tomatoes, onions, and homemade tzatziki sauce",
                "display_order": 7,
                "variants": _regular("10.05"),
            },
            {
                "name": "Chicken Gyro",
                "description": "Marinated chicken, tomatoes, onions, and homemade tzatziki sauce",
                "display_order": 8,
                "variants": _regular("12.05"),
            },
            {
                "name": "Char-Broiled Chicken",
                "display_order": 9,
                "variants": _regular("10.35"),
            },
            {
                "name": "Veggie Burger",
                "display_order": 10,
                "variants": _regular("6.05"),
            },
            {
                "name": "Turkey Burger",
                "display_order": 11,
                "variants": _regular("6.95"),
            },
            {
                "name": "4oz. Junior Burger",
                "display_order": 12,
                "variants": _regular("4.05"),
            },
            {
                "name": "4oz. Junior Chicken",
                "display_order": 13,
                "variants": _regular("5.35"),
            },
            {
                "name": "Beyond Burger",
                "description": "1/4 lb burger",
                "display_order": 14,
                "variants": _regular("8.75"),
            },
            {
                "name": "Grilled Cheese",
                "description": "Served with a bag of chips and a pickle",
                "display_order": 15,
                "variants": _regular("5.45"),
            },
            {"name": "Tuna Melt", "display_order": 16, "variants": _regular("12.45")},
            {
                "name": "Super Chicken",
                "description": "Homemade fried chicken breast sandwich",
                "display_order": 17,
                "variants": _regular("10.35"),
            },
            {
                "name": "Junior Char Chicken",
                "description": "Homemade fried chicken breast sandwich",
                "display_order": 18,
                "variants": _regular("5.35"),
            },
            {
                "name": "Hot Honey Salmon",
                "display_order": 19,
                "variants": _regular("11.95"),
            },
        ],
    },
    {
        "name": "Wing Dings",
        "display_order": 3,
        "items": [
            {
                "name": "Garlic Parmesan",
                "display_order": 1,
                "variants": _sizes(
                    ("Medium", "12.25"), ("Large", "22.75"), ("X-Large", "33.65")
                ),
            },
            {
                "name": "Wing Ding",
                "display_order": 2,
                "variants": _sizes(
                    ("Medium", "11.60"), ("Large", "21.95"), ("X-Large", "32.45")
                ),
            },
            {
                "name": "Buffalo Wing Ding",
                "display_order": 3,
                "variants": _sizes(
                    ("Medium", "12.25"), ("Large", "22.75"), ("X-Large", "33.65")
                ),
            },
            {
                "name": "Teriyaki Wing Ding",
                "display_order": 4,
                "variants": _sizes(
                    ("Medium", "12.25"), ("Large", "22.75"), ("X-Large", "33.65")
                ),
            },
            {
                "name": "Sweet Asian Chili Wing Ding",
                "display_order": 5,
                "variants": _sizes(
                    ("Medium", "12.25"), ("Large", "22.75"), ("X-Large", "33.65")
                ),
            },
            {
                "name": "Sweet Buffalo Wing Ding",
                "display_order": 6,
                "variants": _sizes(
                    ("Medium", "12.25"), ("Large", "22.75"), ("X-Large", "33.65")
                ),
            },
            {
                "name": "Gold Rush Wing Ding",
                "display_order": 7,
                "variants": _sizes(
                    ("Medium", "12.25"), ("Large", "22.75"), ("X-Large", "33.65")
                ),
            },
        ],
    },
    {
        "name": "Homemade Wings",
        "display_order": 4,
        "items": [
            {
                "name": "Chicken Fingers",
                "display_order": 1,
                "variants": _sizes(
                    ("Medium", "9.55"), ("Large", "14.50"), ("X-Large", "20.30")
                ),
            },
            {
                "name": "Boneless Buffalo",
                "display_order": 2,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Boneless Teriyaki",
                "display_order": 3,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Boneless Sweet Buffalo",
                "display_order": 4,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Boneless Sweet Asian",
                "display_order": 5,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Boneless Gold Rush",
                "display_order": 6,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Boneless Garlic Parmesan",
                "display_order": 7,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Garlic Parmesan Wing",
                "display_order": 8,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Chicken Wing",
                "display_order": 9,
                "variants": _sizes(
                    ("Medium", "9.55"), ("Large", "14.50"), ("X-Large", "20.30")
                ),
            },
            {
                "name": "Buffalo Wing",
                "display_order": 10,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Sweet Asian Chili Wing",
                "display_order": 11,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Sweet Buffalo Wing",
                "display_order": 12,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Teriyaki Wing",
                "display_order": 13,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
            {
                "name": "Gold Rush Wing",
                "display_order": 14,
                "variants": _sizes(
                    ("Medium", "10.55"), ("Large", "16.05"), ("X-Large", "21.99")
                ),
            },
        ],
    },
    {
        "name": "Georgio's Club Sandwiches",
        "display_order": 5,
        "description": "Triple decker on white, wheat, or marble rye with lettuce, tomato, mayo, bacon, choice of side, and pickle spear.",
        "items": [
            {
                "name": "Roasted Turkey Club",
                "display_order": 1,
                "variants": _regular("13.95"),
            },
            {
                "name": "Ham & Cheese Club",
                "display_order": 2,
                "variants": _regular("13.95"),
            },
            {
                "name": "Albacore White Tuna Club",
                "display_order": 3,
                "variants": _regular("15.95"),
            },
            {
                "name": "Chicken Salad Club",
                "display_order": 4,
                "variants": _regular("15.35"),
            },
            {
                "name": "Roast Beef Club",
                "display_order": 5,
                "variants": _regular("15.95"),
            },
            {
                "name": "Grilled Chicken Club",
                "display_order": 6,
                "variants": _regular("15.35"),
            },
            {"name": "Hamburger", "display_order": 7, "variants": _regular("13.95")},
            {"name": "BLT", "display_order": 8, "variants": _regular("14.75")},
            {"name": "Egg Salad", "display_order": 9, "variants": _regular("14.95")},
        ],
    },
    {
        "name": "Omelette Subs",
        "display_order": 6,
        "items": [
            {
                "name": "Egg & Cheese",
                "display_order": 1,
                "variants": _sizes(("Small", "8.75"), ("Large", "9.95")),
            },
            {
                "name": "Pepper & Egg",
                "display_order": 2,
                "variants": _sizes(("Small", "8.75"), ("Large", "9.95")),
            },
            {
                "name": "Ham, Egg, & Cheese",
                "display_order": 3,
                "variants": _sizes(("Small", "9.75"), ("Large", "11.95")),
            },
            {
                "name": "Western",
                "description": "Ham, onions & American cheese",
                "display_order": 4,
                "variants": _sizes(("Small", "10.45"), ("Large", "12.10")),
            },
            {
                "name": "Bacon, Egg, & Cheese",
                "display_order": 5,
                "variants": _sizes(("Small", "10.95"), ("Large", "12.65")),
            },
            {
                "name": "Sausage, Egg, & Cheese",
                "display_order": 6,
                "variants": _sizes(("Small", "10.95"), ("Large", "12.65")),
            },
            {
                "name": "Potato, Egg, & Cheese",
                "display_order": 7,
                "variants": _sizes(("Small", "10.25"), ("Large", "12.10")),
            },
            {
                "name": "Grecian",
                "description": "Feta, spinach, tomato & onion",
                "display_order": 8,
                "variants": _sizes(("Small", "11.15"), ("Large", "12.75")),
            },
            {
                "name": "Steak & Egg",
                "display_order": 9,
                "variants": _sizes(("Small", "14.35"), ("Large", "17.45")),
            },
        ],
    },
    {
        "name": "Dinners",
        "display_order": 7,
        "description": "Served with choice of side and a garden salad.",
        "items": [
            {
                "name": "Chicken Kabob",
                "display_order": 1,
                "variants": _regular("16.60"),
            },
            {
                "name": "Georgio's Famous Steak Tip",
                "display_order": 2,
                "variants": _regular("24.25"),
            },
            {
                "name": "Georgio's Famous Honey BBQ Steak Tip",
                "display_order": 3,
                "variants": _regular("25.25"),
            },
            {"name": "Turkey Tips", "display_order": 4, "variants": _regular("16.60")},
            {
                "name": "Teriyaki Turkey Tips",
                "display_order": 5,
                "variants": _regular("17.10"),
            },
            {
                "name": "Georgio's Famous Super Beef",
                "display_order": 6,
                "variants": _regular("17.60"),
            },
            {
                "name": "Georgio's Famous Roast Beef",
                "display_order": 7,
                "variants": _regular("16.50"),
            },
            {
                "name": "Homemade Hamburger",
                "display_order": 8,
                "variants": _regular("13.95"),
            },
            {
                "name": "Homemade Cheeseburger",
                "display_order": 9,
                "variants": _regular("15.95"),
            },
            {"name": "Pastrami", "display_order": 10, "variants": _regular("17.45")},
            {
                "name": "Chicken Finger",
                "display_order": 11,
                "variants": _regular("15.45"),
            },
            {
                "name": "Chicken Wing",
                "display_order": 12,
                "variants": _regular("15.45"),
            },
            {
                "name": "Char Broiled Chicken Breast",
                "display_order": 13,
                "variants": _regular("18.25"),
            },
            {
                "name": "Buffalo Finger",
                "display_order": 14,
                "variants": _regular("16.45"),
            },
            {
                "name": "Buffalo Wing",
                "display_order": 15,
                "variants": _regular("16.45"),
            },
            {"name": "Gyro", "display_order": 16, "variants": _regular("14.10")},
            {
                "name": "Chicken Gyro",
                "display_order": 17,
                "variants": _regular("16.10"),
            },
            {
                "name": "Teriyaki Shrimp Stir Fry",
                "description": "Grilled shrimp in homemade teriyaki over rice and salad with mushrooms, peppers, onions, and broccoli",
                "display_order": 18,
                "variants": _regular("18.65"),
            },
            {
                "name": "Jumbo Wing Ding",
                "display_order": 19,
                "variants": _regular("18.45"),
            },
            {
                "name": "Georgio's Famous Teriyaki Chicken Kabob",
                "display_order": 20,
                "variants": _regular("17.60"),
            },
            {
                "name": "Homemade Fried Chicken Breast",
                "description": "Three 4 oz. fresh chicken breasts battered in homemade seasonings and fried",
                "display_order": 21,
                "variants": _regular("18.25"),
            },
            {
                "name": "Beyond Burger",
                "description": "1/4 lb burger",
                "display_order": 22,
                "variants": _regular("14.35"),
            },
            {
                "name": "Fried Shrimp Basket",
                "description": "Served with steak fries, coleslaw & homemade tartar sauce",
                "display_order": 23,
                "variants": _regular("15.45"),
            },
        ],
    },
    {
        "name": "Seafood",
        "display_order": 8,
        "items": [
            {
                "name": "Broiled Haddock Plate",
                "description": "Served with choice of side and a salad",
                "display_order": 1,
                "variants": _regular("24.35"),
            },
            {
                "name": "Fried Haddock Plate",
                "description": "Served with choice of side and a salad; homemade tartar sauce included",
                "display_order": 2,
                "variants": _regular("24.35"),
            },
            {
                "name": "Fish & Chips",
                "description": "Served with steak fries, coleslaw, homemade tartar sauce & lemon wedge",
                "display_order": 3,
                "variants": _regular("17.10"),
            },
            {
                "name": "Haddock Sandwich Dinner",
                "description": "Served with choice of side and a salad",
                "display_order": 4,
                "variants": _regular("18.25"),
            },
            {
                "name": "Haddock Sandwich",
                "display_order": 5,
                "variants": _regular("12.10"),
            },
            {
                "name": "Fried Shrimp Basket",
                "description": "Served with steak fries, coleslaw & homemade tartar sauce",
                "display_order": 6,
                "variants": _regular("15.45"),
            },
            {
                "name": "Fried Fish Basket",
                "description": "Fresh haddock & shrimp with steak fries, coleslaw, homemade tartar sauce & lemon wedge",
                "display_order": 7,
                "variants": _regular("23.25"),
            },
            {
                "name": "Broiled Salmon",
                "description": "Served with choice of side and a salad",
                "display_order": 8,
                "variants": _regular("19.10"),
            },
            {
                "name": "Hot Honey Salmon Sandwich",
                "description": "Grilled salmon, pickles & homemade coleslaw with hot honey on a grilled seeded roll",
                "display_order": 9,
                "variants": _regular("12.25"),
            },
        ],
    },
    {
        "name": "Dessert Calzones",
        "display_order": 9,
        "items": [
            {"name": "Smores", "display_order": 1, "variants": _regular("9.95")},
            {"name": "Fluffanutter", "display_order": 2, "variants": _regular("9.95")},
            {"name": "Nutella", "display_order": 3, "variants": _regular("9.95")},
            {
                "name": "Peanut Butter Cup",
                "display_order": 4,
                "variants": _regular("9.95"),
            },
            {"name": "Milky Way", "display_order": 5, "variants": _regular("9.95")},
            {
                "name": "Salted Caramel",
                "display_order": 6,
                "variants": _regular("9.95"),
            },
        ],
    },
    {
        "name": "Mac & Cheese Station",
        "display_order": 10,
        "description": "Homemade; served with garlic bread.",
        "items": [
            {"name": "Mac & Cheese", "display_order": 1, "variants": _regular("10.25")},
            {
                "name": "Buffalo Chicken",
                "display_order": 2,
                "variants": _regular("14.95"),
            },
            {
                "name": "Chicken Kabob",
                "display_order": 3,
                "variants": _regular("14.95"),
            },
            {"name": "Steak Tip", "display_order": 4, "variants": _regular("20.25")},
            {
                "name": "Honey BBQ Steak Tip",
                "display_order": 5,
                "variants": _regular("20.27"),
            },
            {
                "name": "Grilled Shrimp",
                "display_order": 6,
                "variants": _regular("17.25"),
            },
            {
                "name": "Hot Honey Salmon",
                "display_order": 7,
                "variants": _regular("17.65"),
            },
        ],
    },
    {
        "name": "Calzones",
        "display_order": 11,
        "items": [
            {
                "name": "Spinach & Cheese",
                "display_order": 1,
                "variants": _sizes(
                    ("Individual", "15.90"),
                    ("Small", "20.75"),
                    ("Large", "29.95"),
                    ("X-Large", "38.25"),
                ),
            },
            {
                "name": "Veggie",
                "display_order": 2,
                "variants": _sizes(
                    ("Individual", "15.90"),
                    ("Small", "20.75"),
                    ("Large", "29.95"),
                    ("X-Large", "38.25"),
                ),
            },
            {
                "name": "Ham & Cheese",
                "display_order": 3,
                "variants": _sizes(
                    ("Individual", "15.90"),
                    ("Small", "20.75"),
                    ("Large", "29.95"),
                    ("X-Large", "38.25"),
                ),
            },
            {
                "name": "Italian",
                "display_order": 4,
                "variants": _sizes(
                    ("Individual", "15.90"),
                    ("Small", "20.75"),
                    ("Large", "29.95"),
                    ("X-Large", "38.25"),
                ),
            },
            {
                "name": "Buffalo Mac & Cheese",
                "display_order": 5,
                "variants": _sizes(
                    ("Individual", "17.50"),
                    ("Small", "23.35"),
                    ("Large", "34.25"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "BBQ Chicken",
                "display_order": 6,
                "variants": _sizes(
                    ("Individual", "17.50"),
                    ("Small", "23.35"),
                    ("Large", "34.25"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "Chicken Kabob",
                "description": "Grilled chicken, tomatoes, onions, feta, mozzarella & Greek dressing",
                "display_order": 7,
                "variants": _sizes(
                    ("Individual", "17.50"),
                    ("Small", "23.35"),
                    ("Large", "34.25"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "Chicken Broccoli",
                "description": "Grilled chicken, fresh broccoli & pizza cheese",
                "display_order": 8,
                "variants": _sizes(
                    ("Individual", "17.50"),
                    ("Small", "23.35"),
                    ("Large", "34.25"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "Steak Bomb",
                "description": "Shredded steak, mushrooms, peppers, onions, salami & pizza cheese",
                "display_order": 9,
                "variants": _sizes(
                    ("Individual", "19.95"),
                    ("Small", "24.95"),
                    ("Large", "37.35"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "Chicken Parmesan",
                "display_order": 10,
                "variants": _sizes(
                    ("Individual", "17.50"),
                    ("Small", "23.35"),
                    ("Large", "34.25"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "Buffalo Chicken",
                "display_order": 11,
                "variants": _sizes(
                    ("Individual", "17.50"),
                    ("Small", "23.35"),
                    ("Large", "34.25"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "Meatball",
                "display_order": 12,
                "variants": _sizes(
                    ("Individual", "17.50"),
                    ("Small", "23.35"),
                    ("Large", "34.25"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "Steak & Cheese",
                "display_order": 13,
                "variants": _sizes(
                    ("Individual", "18.95"),
                    ("Small", "24.95"),
                    ("Large", "35.95"),
                    ("X-Large", "46.75"),
                ),
            },
            {
                "name": "Cheeseburger",
                "display_order": 14,
                "variants": _sizes(
                    ("Individual", "17.50"),
                    ("Small", "23.35"),
                    ("Large", "34.25"),
                    ("X-Large", "44.75"),
                ),
            },
            {
                "name": "Pastrami",
                "display_order": 15,
                "variants": _sizes(
                    ("Individual", "18.95"),
                    ("Small", "24.95"),
                    ("Large", "35.95"),
                    ("X-Large", "46.75"),
                ),
            },
            {
                "name": "Honey BBQ Steak Tip",
                "display_order": 16,
                "variants": _sizes(
                    ("Individual", "37.95"),
                    ("Small", "52.95"),
                    ("Large", "74.95"),
                    ("X-Large", "99.95"),
                ),
            },
        ],
    },
    {
        "name": "Pasta Dishes",
        "display_order": 12,
        "description": "Served with garlic bread, choice of homemade marinara or alfredo, and choice of spaghetti, ziti, or cellentani.",
        "items": [
            {"name": "With Sauce", "display_order": 1, "variants": _regular("9.65")},
            {
                "name": "With Meatballs",
                "display_order": 2,
                "variants": _regular("12.45"),
            },
            {
                "name": "With Sweet Italian Sausage",
                "display_order": 3,
                "variants": _regular("12.45"),
            },
            {
                "name": "With Linguica",
                "display_order": 4,
                "variants": _regular("12.45"),
            },
            {
                "name": "With Homemade Chicken Cutlet",
                "display_order": 5,
                "variants": _regular("14.60"),
            },
            {
                "name": "With Homemade Eggplant",
                "display_order": 6,
                "variants": _regular("12.45"),
            },
            {
                "name": "With Chicken Broccoli Alfredo",
                "display_order": 7,
                "variants": _regular("15.75"),
            },
            {
                "name": "With Grilled Shrimp",
                "display_order": 8,
                "variants": _regular("17.20"),
            },
            {
                "name": "With Grilled Shrimp Broccoli Alfredo",
                "description": "In homemade alfredo sauce",
                "display_order": 9,
                "variants": _regular("17.20"),
            },
            {
                "name": "Shrimp Scampi",
                "display_order": 10,
                "variants": _regular("17.20"),
            },
            {
                "name": "Cheese Ravioli (8 pieces)",
                "display_order": 11,
                "variants": _regular("11.65"),
            },
            {
                "name": "Stuffed Shells (6 pieces)",
                "display_order": 12,
                "variants": _regular("11.65"),
            },
        ],
    },
    {
        "name": "Pizzas",
        "display_order": 13,
        "items": [
            {
                "name": "Cheese",
                "display_order": 1,
                "variants": _sizes(
                    ("Small", "10.85"),
                    ("Large", "14.95"),
                    ("X-Large (Sicilian)", "20.75"),
                ),
            },
            {
                "name": "1 Topping",
                "display_order": 2,
                "variants": _sizes(
                    ("Small", "12.15"),
                    ("Large", "16.25"),
                    ("X-Large (Sicilian)", "22.25"),
                ),
            },
            {
                "name": "2 Toppings",
                "display_order": 3,
                "variants": _sizes(
                    ("Small", "13.15"),
                    ("Large", "17.25"),
                    ("X-Large (Sicilian)", "23.25"),
                ),
            },
            {
                "name": "3 Toppings",
                "display_order": 4,
                "variants": _sizes(
                    ("Small", "14.15"),
                    ("Large", "18.25"),
                    ("X-Large (Sicilian)", "24.25"),
                ),
            },
            {
                "name": "4 Toppings",
                "display_order": 5,
                "variants": _sizes(
                    ("Small", "15.15"),
                    ("Large", "19.25"),
                    ("X-Large (Sicilian)", "25.25"),
                ),
            },
        ],
    },
    {
        "name": "Specialty Pizzas",
        "display_order": 14,
        "items": [
            {
                "name": "The Favorite",
                "description": "Official blend of cheeses with a slightly sweeter sauce",
                "display_order": 1,
                "variants": _sizes(
                    ("Small", "10.85"), ("Large", "14.95"), ("X-Large", "20.75")
                ),
            },
            {
                "name": "Shrimp Scampi",
                "description": "Shrimp, olive oil, fresh garlic & blend of cheeses",
                "display_order": 2,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Ziti Shrimp Alfredo",
                "description": "Shrimp with ziti in homemade alfredo sauce & blend of cheeses",
                "display_order": 3,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "The Melanzana",
                "description": "Fried eggplant, ricotta, caramelized onions, sweeter sauce & blend of cheeses",
                "display_order": 4,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Porky",
                "description": "Ricotta cheese & sweet Italian sausage",
                "display_order": 5,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "House Special",
                "description": "Pepperoni, hamburger, sausage, salami, peppers, onions & mushrooms",
                "display_order": 6,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Grilled Kabob",
                "description": "Grilled chicken, feta, tomato & onions",
                "display_order": 7,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Veggie Supreme",
                "description": "Peppers, onions, mushrooms, fresh tomato & broccoli",
                "display_order": 8,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Polo Primavera",
                "description": "Grilled chicken, broccoli, ham & onion with homemade alfredo sauce",
                "display_order": 9,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Grecian",
                "description": "Feta, spinach, black olives, tomato & onion with homemade alfredo sauce",
                "display_order": 10,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "BBQ Chicken",
                "description": "Grilled chicken & BBQ sauce",
                "display_order": 11,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Buffalo Chicken",
                "description": "Buffalo chicken tenders, homemade buffalo sauce & blend of cheeses",
                "display_order": 12,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Meatlover's Pizza",
                "description": "Pepperoni, ham, salami, hamburger, sausage, bacon & linguica",
                "display_order": 13,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Mac & Cheese",
                "description": "Cellentani pasta, homemade cheddar cheese sauce & blend of cheeses",
                "display_order": 14,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Hot Honey Chicken",
                "description": "Fried chicken, pepperoni, bacon & caramelized onions with hot honey",
                "display_order": 15,
                "variants": _sizes(
                    ("Small", "17.95"), ("Large", "23.75"), ("X-Large", "30.95")
                ),
            },
            {
                "name": "Ch. Broccoli Alfredo",
                "description": "Grilled chicken, broccoli & homemade alfredo sauce",
                "display_order": 16,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Hawaiian",
                "description": "Ham, pineapple & onion",
                "display_order": 17,
                "variants": _sizes(
                    ("Small", "14.15"), ("Large", "18.25"), ("X-Large", "24.25")
                ),
            },
            {
                "name": "White Pizza",
                "description": "Olive oil, fresh garlic & blend of cheeses",
                "display_order": 18,
                "variants": _sizes(
                    ("Small", "14.95"), ("Large", "19.95"), ("X-Large", "25.95")
                ),
            },
            {
                "name": "Spinach & Artichoke Alfredo",
                "description": "Homemade alfredo, spinach, artichokes & blend of cheeses",
                "display_order": 19,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Polynesian",
                "description": "Ham, bacon, pineapple, caramelized onions & blend of cheeses",
                "display_order": 20,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Just Chicken",
                "description": "Chicken kabob & blend of cheeses",
                "display_order": 21,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Rio Rodeo",
                "description": "BBQ sauce, shredded steak, bacon & blend of cheeses",
                "display_order": 22,
                "variants": _sizes(
                    ("Small", "17.25"), ("Large", "23.75"), ("X-Large", "30.95")
                ),
            },
            {
                "name": "The Spicy Taco",
                "description": "Buffalo sauce, hamburger, tomato, cheese blend & fresh lettuce",
                "display_order": 23,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Garden Pesto",
                "description": "Pizza sauce, roasted red peppers, spinach, onions, eggplant, mushrooms, tomatoes, pesto & cheese blend",
                "display_order": 24,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Pollo Pesto",
                "description": "Pesto, chicken kabob, broccoli & cheese blend",
                "display_order": 25,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Margarita Pizza",
                "description": "Fresh mozzarella, basil, garlic, olive oil & sliced tomato",
                "display_order": 26,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "21.95"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Gluten Free Pizza",
                "display_order": 27,
                "variants": _regular("18.65"),
            },
            {
                "name": "Buffalo Chicken Mac & Cheese",
                "description": "Buffalo chicken tenders, cellentani, cheddar cheese sauce & cheese blend",
                "display_order": 28,
                "variants": _sizes(
                    ("Small", "15.95"), ("Large", "20.75"), ("X-Large", "28.95")
                ),
            },
            {
                "name": "Steak & Cheese",
                "description": "Pizza sauce, shredded steak & blend of cheeses",
                "display_order": 29,
                "variants": _sizes(
                    ("Small", "17.25"), ("Large", "23.75"), ("X-Large", "30.95")
                ),
            },
        ],
    },
    {
        "name": "Salads",
        "display_order": 15,
        "description": "All salads come with pita bread and a dressing of choice.",
        "items": [
            {
                "name": "Garden Salad",
                "description": "Iceberg lettuce, cherry tomatoes, green peppers, cucumber, carrots, red cabbage & kalamata olives",
                "display_order": 1,
                "variants": _regular("9.10"),
            },
            {
                "name": "Greek Salad",
                "description": "Garden-style salad finished with crumbled feta",
                "display_order": 2,
                "variants": _regular("11.10"),
            },
            {
                "name": "Caesar Salad",
                "description": "Romaine lettuce, croutons & shredded parmesan",
                "display_order": 3,
                "variants": _regular("10.10"),
            },
            {
                "name": "Antipasto",
                "description": "Mortadella, salami, capicola & provolone",
                "display_order": 4,
                "variants": _regular("11.75"),
            },
            {
                "name": "Chef",
                "description": "Turkey, ham, bologna & American cheese",
                "display_order": 5,
                "variants": _regular("11.75"),
            },
            {
                "name": "Buffalo Finger",
                "display_order": 6,
                "variants": _regular("14.25"),
            },
            {"name": "Tuna", "display_order": 7, "variants": _regular("14.65")},
            {
                "name": "Buffalo Kabob",
                "display_order": 8,
                "variants": _regular("14.95"),
            },
            {
                "name": "Tri Color Quinoa Salad",
                "description": "Quinoa, arugula, hummus, avocado, red onions & beets with balsamic vinaigrette",
                "display_order": 9,
                "variants": _regular("13.45"),
            },
            {
                "name": "Apple Beet Salad",
                "description": "Arugula, pecans, Granny Smith apple, beets & goat cheese with honey lemon vinaigrette",
                "display_order": 10,
                "variants": _regular("14.25"),
            },
            {
                "name": "Clubhouse Salad",
                "description": "Grilled chicken, iceberg lettuce, tomatoes, cucumbers, carrots, olives, cabbage, bacon, mozzarella & hard-boiled egg",
                "display_order": 11,
                "variants": _regular("16.25"),
            },
            {
                "name": "Baby Spinach Salad",
                "description": "Baby spinach, feta, bacon & walnuts with raspberry vinaigrette",
                "display_order": 12,
                "variants": _regular("13.65"),
            },
            {
                "name": "Wedge Salad",
                "description": "Iceberg lettuce, tomatoes, bacon & blue cheese with blue cheese dressing",
                "display_order": 13,
                "variants": _regular("12.45"),
            },
            {
                "name": "Power Salad",
                "description": "Spring mix, egg, avocado, dried cranberries, walnuts, bacon & goat cheese",
                "display_order": 14,
                "variants": _regular("15.25"),
            },
            {
                "name": "Arugula Salad",
                "description": "Arugula, roasted red peppers, parmesan, croutons & avocado with honey lemon vinaigrette",
                "display_order": 15,
                "variants": _regular("14.65"),
            },
            {
                "name": "Grilled Shrimp Salad",
                "display_order": 16,
                "variants": _regular("15.25"),
            },
            {
                "name": "Grilled Salmon Salad",
                "display_order": 17,
                "variants": _regular("16.95"),
            },
            {
                "name": "Chicken Salad",
                "display_order": 18,
                "variants": _regular("12.35"),
            },
            {
                "name": "Crab Meat Salad",
                "display_order": 19,
                "variants": _regular("11.45"),
            },
            {
                "name": "Chicken Kabob",
                "display_order": 20,
                "variants": _regular("13.95"),
            },
            {
                "name": "Chicken Caesar",
                "display_order": 21,
                "variants": _regular("14.35"),
            },
            {"name": "Steak Tip", "display_order": 22, "variants": _regular("20.15")},
            {
                "name": "Steak Tip Caesar",
                "display_order": 23,
                "variants": _regular("21.15"),
            },
            {
                "name": "Honey BBQ Steak Tip Salad",
                "display_order": 24,
                "variants": _regular("21.15"),
            },
            {
                "name": "Honey BBQ Steak Tip Caesar Salad",
                "display_order": 25,
                "variants": _regular("21.95"),
            },
            {"name": "Turkey Tip", "display_order": 26, "variants": _regular("13.65")},
            {
                "name": "Teriyaki Turkey Tip",
                "display_order": 27,
                "variants": _regular("14.25"),
            },
            {
                "name": "Georgio's Famous Teriyaki Chicken Kabob",
                "display_order": 28,
                "variants": _regular("14.95"),
            },
            {"name": "Roast Beef", "display_order": 29, "variants": _regular("14.65")},
            {
                "name": "Homemade Egg Salad",
                "display_order": 30,
                "variants": _regular("11.55"),
            },
            {
                "name": "Cabbage Crunch",
                "description": "Red & green cabbage, carrots, pecans, avocado, green apple & dried cranberries with honey lemon vinaigrette",
                "display_order": 31,
                "variants": _regular("15.25"),
            },
        ],
    },
    {
        "name": "Cold Subs",
        "display_order": 16,
        "items": [
            {
                "name": "Ham & Cheese",
                "display_order": 1,
                "variants": _sizes(
                    ("Sandwich", "7.55"), ("Small", "9.10"), ("Large", "11.95")
                ),
            },
            {
                "name": "Italian",
                "description": "Mortadella, salami, capicola, provolone, oregano & olive oil",
                "display_order": 2,
                "variants": _sizes(
                    ("Sandwich", "7.55"), ("Small", "9.10"), ("Large", "11.95")
                ),
            },
            {
                "name": "American",
                "description": "Ham, bologna, mortadella & American cheese",
                "display_order": 3,
                "variants": _sizes(
                    ("Sandwich", "7.55"), ("Small", "9.10"), ("Large", "11.95")
                ),
            },
            {
                "name": "Genoa Salami w/ Provolone",
                "display_order": 4,
                "variants": _sizes(
                    ("Sandwich", "7.55"), ("Small", "9.10"), ("Large", "11.95")
                ),
            },
            {
                "name": "Roasted Turkey",
                "display_order": 5,
                "variants": _sizes(
                    ("Sandwich", "7.75"), ("Small", "9.45"), ("Large", "12.45")
                ),
            },
            {
                "name": "Albacore White Tuna Fish",
                "display_order": 6,
                "variants": _sizes(
                    ("Sandwich", "9.55"), ("Small", "11.25"), ("Large", "14.45")
                ),
            },
            {
                "name": "Crab Meat",
                "display_order": 7,
                "variants": _sizes(
                    ("Sandwich", "8.55"), ("Small", "9.95"), ("Large", "11.95")
                ),
            },
            {
                "name": "Homemade Chicken Salad",
                "display_order": 8,
                "variants": _sizes(
                    ("Sandwich", "9.25"), ("Small", "10.75"), ("Large", "12.95")
                ),
            },
            {
                "name": "Veggie",
                "description": "Lettuce, tomatoes, pickles, onions & American cheese",
                "display_order": 9,
                "variants": _sizes(
                    ("Sandwich", "7.25"), ("Small", "8.95"), ("Large", "10.95")
                ),
            },
            {
                "name": "Bologna & Cheese",
                "display_order": 10,
                "variants": _sizes(
                    ("Sandwich", "7.55"), ("Small", "9.10"), ("Large", "11.95")
                ),
            },
            {
                "name": "Homemade Egg Salad",
                "display_order": 11,
                "variants": _sizes(
                    ("Sandwich", "7.75"), ("Small", "9.45"), ("Large", "12.45")
                ),
            },
        ],
    },
    {
        "name": "Hot Subs",
        "display_order": 17,
        "items": [
            {
                "name": "Plain Steak",
                "display_order": 1,
                "variants": _sizes(("Small", "10.25"), ("Large", "12.35")),
            },
            {
                "name": "Cheese Steak",
                "display_order": 2,
                "variants": _sizes(("Small", "12.25"), ("Large", "14.85")),
            },
            {
                "name": "Onion Steak",
                "display_order": 3,
                "variants": _sizes(("Small", "10.95"), ("Large", "13.35")),
            },
            {
                "name": "Pepper Steak",
                "display_order": 4,
                "variants": _sizes(("Small", "10.95"), ("Large", "13.35")),
            },
            {
                "name": "Mushroom Steak",
                "display_order": 5,
                "variants": _sizes(("Small", "10.95"), ("Large", "13.35")),
            },
            {
                "name": "Steak Bomb",
                "description": "Mushrooms, peppers, onions, salami & American cheese",
                "display_order": 6,
                "variants": _sizes(("Small", "14.25"), ("Large", "17.25")),
            },
            {
                "name": "Steak & Egg",
                "display_order": 7,
                "variants": _sizes(("Small", "14.25"), ("Large", "17.25")),
            },
            {
                "name": "Georgio's Famous Honey BBQ Steak Tip",
                "description": "With American cheese",
                "display_order": 8,
                "variants": _sizes(("Small", "16.95"), ("Large", "20.10")),
            },
            {
                "name": "Georgio's Famous Steak Tip",
                "description": "With American cheese",
                "display_order": 9,
                "variants": _sizes(("Small", "16.95"), ("Large", "20.10")),
            },
            {
                "name": "Turkey Tip",
                "description": "With American cheese",
                "display_order": 10,
                "variants": _sizes(("Small", "11.10"), ("Large", "13.25")),
            },
            {
                "name": "Teriyaki Turkey Tip",
                "description": "With American cheese",
                "display_order": 11,
                "variants": _sizes(("Small", "11.65"), ("Large", "13.65")),
            },
            {
                "name": "Meatball",
                "description": "With provolone cheese",
                "display_order": 12,
                "variants": _sizes(("Small", "11.25"), ("Large", "13.75")),
            },
            {
                "name": "Sweet Italian Sausage",
                "description": "With provolone cheese",
                "display_order": 13,
                "variants": _sizes(("Small", "9.85"), ("Large", "12.10")),
            },
            {
                "name": "Chicken Finger",
                "display_order": 14,
                "variants": _sizes(("Small", "10.45"), ("Large", "13.25")),
            },
            {
                "name": "Chicken Kabob",
                "description": "With feta cheese",
                "display_order": 15,
                "variants": _sizes(("Small", "11.45"), ("Large", "13.95")),
            },
            {
                "name": "Pastrami",
                "display_order": 16,
                "variants": _sizes(("Small", "13.10"), ("Large", "15.25")),
            },
            {
                "name": "Linguica",
                "display_order": 17,
                "variants": _sizes(("Small", "9.85"), ("Large", "12.10")),
            },
            {
                "name": "Georgio's Homemade Chicken Parmesan",
                "display_order": 18,
                "variants": _sizes(("Small", "11.95"), ("Large", "14.25")),
            },
            {
                "name": "Buffalo Finger",
                "display_order": 19,
                "variants": _sizes(("Small", "11.20"), ("Large", "13.95")),
            },
            {
                "name": "Chicken Bomb",
                "description": "Mushrooms, peppers, onions & American cheese",
                "display_order": 20,
                "variants": _sizes(("Small", "13.20"), ("Large", "15.65")),
            },
            {
                "name": "Homemade Hamburger",
                "display_order": 21,
                "variants": _sizes(("Small", "9.10"), ("Large", "11.75")),
            },
            {
                "name": "Homemade Cheeseburger",
                "display_order": 22,
                "variants": _sizes(("Small", "11.10"), ("Large", "13.25")),
            },
            {
                "name": "Veggie Burger",
                "display_order": 23,
                "variants": _sizes(("Small", "8.95"), ("Large", "10.95")),
            },
            {
                "name": "Turkey Burger",
                "display_order": 24,
                "variants": _sizes(("Small", "9.45"), ("Large", "11.75")),
            },
            {
                "name": "BLT",
                "description": "Bacon, lettuce & tomatoes on a grilled sub roll",
                "display_order": 25,
                "variants": _sizes(("Small", "10.10"), ("Large", "12.95")),
            },
            {
                "name": "Veggie",
                "description": "Grilled mushrooms, peppers, onions, broccoli & American cheese",
                "display_order": 26,
                "variants": _sizes(("Small", "8.35"), ("Large", "10.10")),
            },
            {
                "name": "Georgio's Homemade Eggplant Parmesan",
                "display_order": 27,
                "variants": _sizes(("Small", "8.95"), ("Large", "11.35")),
            },
            {
                "name": "Georgio's Homemade Chicken Cutlet",
                "description": "With provolone cheese",
                "display_order": 28,
                "variants": _sizes(("Small", "11.95"), ("Large", "14.25")),
            },
            {
                "name": "Buffalo Kabob",
                "display_order": 29,
                "variants": _sizes(("Small", "11.95"), ("Large", "14.65")),
            },
            {
                "name": "Georgio's Famous Teriyaki Chicken Kabob",
                "display_order": 30,
                "variants": _sizes(("Small", "11.95"), ("Large", "14.65")),
            },
            {
                "name": "Fried Haddock",
                "display_order": 31,
                "variants": _sizes(("Small", "18.75"), ("Large", "23.95")),
            },
            {
                "name": "Beyond Burger",
                "description": "1/4 lb burger",
                "display_order": 32,
                "variants": _sizes(("Small", "12.20"), ("Large", "17.99")),
            },
            {
                "name": "Shrimp Po Boy",
                "description": "Fried shrimp in Sweet Asian Chili sauce with tomatoes, pickles & homemade coleslaw",
                "display_order": 33,
                "variants": _sizes(("Small", "13.25"), ("Large", "16.10")),
            },
        ],
    },
    {
        "name": "Wraps",
        "display_order": 18,
        "items": [
            {
                "name": "Spinach Hummus Wrap",
                "description": "Spinach, cucumbers, carrots, tomatoes & avocado with hummus",
                "display_order": 1,
                "variants": _regular("11.25"),
            },
            {
                "name": "Buffalo Chicken",
                "display_order": 2,
                "variants": _regular("13.95"),
            },
            {
                "name": "Chicken Caesar",
                "display_order": 3,
                "variants": _regular("13.95"),
            },
            {
                "name": "Chicken Kabob",
                "display_order": 4,
                "variants": _regular("13.95"),
            },
            {
                "name": "Steak Tip",
                "description": "With cheese",
                "display_order": 5,
                "variants": _regular("20.10"),
            },
            {
                "name": "Honey BBQ Steak Tip",
                "description": "With American cheese",
                "display_order": 6,
                "variants": _regular("20.10"),
            },
            {"name": "Turkey Club", "display_order": 7, "variants": _regular("13.95")},
            {
                "name": "Greek Salad",
                "description": "Iceberg lettuce, tomatoes, olives, feta, red onions & house dressing",
                "display_order": 8,
                "variants": _regular("11.95"),
            },
            {
                "name": "Mediterranean",
                "description": "Iceberg lettuce, tomatoes, olives, onions, peppers, cucumbers, feta & house dressing",
                "display_order": 9,
                "variants": _regular("11.95"),
            },
            {"name": "Tuna", "display_order": 10, "variants": _regular("14.45")},
            {"name": "Roast Beef", "display_order": 11, "variants": _regular("14.95")},
            {
                "name": "Buffalo Kabob",
                "display_order": 12,
                "variants": _regular("14.65"),
            },
        ],
    },
    {
        "name": "Rice Bowls",
        "display_order": 19,
        "description": "All rice bowls are served with rice pilaf.",
        "items": [
            {"name": "Turkey Tip", "display_order": 1, "variants": _regular("11.85")},
            {
                "name": "Teriyaki Turkey Tip",
                "display_order": 2,
                "variants": _regular("12.35"),
            },
            {
                "name": "Honey BBQ Steak Tip",
                "display_order": 3,
                "variants": _regular("20.10"),
            },
            {
                "name": "Teriyaki Chicken",
                "display_order": 4,
                "variants": _regular("12.85"),
            },
            {
                "name": "Grilled Shrimp",
                "display_order": 5,
                "variants": _regular("14.10"),
            },
            {
                "name": "Honey BBQ Steak Tip and Grilled Shrimp Combo",
                "display_order": 6,
                "variants": _regular("20.10"),
            },
            {
                "name": "Vegetarian",
                "description": "Tuscan vegetables & broccoli with rice pilaf",
                "display_order": 7,
                "variants": _regular("9.75"),
            },
            {
                "name": "Char-Broiled Chicken Breast",
                "display_order": 8,
                "variants": _regular("12.95"),
            },
            {"name": "Chicken Wing", "display_order": 9, "variants": _regular("12.10")},
            {
                "name": "Teriyaki Wing",
                "display_order": 10,
                "variants": _regular("12.65"),
            },
            {
                "name": "Chicken Finger",
                "display_order": 11,
                "variants": _regular("12.10"),
            },
            {
                "name": "Buffalo Finger",
                "display_order": 12,
                "variants": _regular("12.65"),
            },
            {"name": "Wing Ding", "display_order": 13, "variants": _regular("13.95")},
            {
                "name": "Buffalo Wing Ding",
                "display_order": 14,
                "variants": _regular("14.50"),
            },
            {
                "name": "Gyro Rice Bowl",
                "description": "Seasoned beef, tomatoes, onions & homemade tzatziki over rice",
                "display_order": 15,
                "variants": _regular("11.25"),
            },
            {
                "name": "Chicken Gyro Rice Bowl",
                "description": "Marinated chicken, tomatoes, onions & homemade tzatziki over rice",
                "display_order": 16,
                "variants": _regular("13.25"),
            },
            {
                "name": "Fried Haddock",
                "display_order": 17,
                "variants": _regular("14.45"),
            },
            {
                "name": "Bang Bang Cauliflower",
                "display_order": 18,
                "variants": _regular("11.10"),
            },
            {
                "name": "Bang Bang Shrimp",
                "display_order": 19,
                "variants": _regular("15.10"),
            },
            {"name": "Meatball", "display_order": 20, "variants": _regular("11.25")},
            {
                "name": "Broiled Salmon",
                "display_order": 21,
                "variants": _regular("15.10"),
            },
        ],
    },
    {
        "name": "Desserts",
        "display_order": 20,
        "items": [
            {"name": "Brownies", "display_order": 1, "variants": _regular("2.90")},
            {"name": "Cookies", "display_order": 2, "variants": _regular("2.90")},
            {"name": "Whoopie Pies", "display_order": 3, "variants": _regular("2.90")},
            {
                "name": "Cinnamon Sticks w/ Frosting",
                "display_order": 4,
                "variants": _regular("5.50"),
            },
            {
                "name": "Homemade Baklava",
                "display_order": 5,
                "variants": _regular("5.95"),
            },
        ],
    },
    {
        "name": "Extras",
        "display_order": 21,
        "items": [
            {
                "name": "Homemade Tartar Sauce",
                "display_order": 1,
                "variants": _regular("1.05"),
            },
            {
                "name": "Set-Ups",
                "description": "Pita bread, house dressing & silverware",
                "display_order": 2,
                "variants": _regular("2.25"),
            },
            {"name": "Cheese & Feta", "display_order": 3, "variants": _regular("2.00")},
            {"name": "Hot Honey", "display_order": 4, "variants": _regular("3.00")},
            {
                "name": "Mini Garlic Pickles (4)",
                "display_order": 5,
                "variants": _regular("1.15"),
            },
            {
                "name": "Bottle of Georgio's Famous Homemade House Dressing",
                "display_order": 6,
                "variants": _regular("5.95"),
            },
            {
                "name": "Homemade Marinara Sauce",
                "display_order": 7,
                "variants": _sizes(("8 oz.", "1.75"), ("16 oz.", "2.75")),
            },
            {
                "name": "Homemade Alfredo Sauce",
                "display_order": 8,
                "variants": _sizes(("8 oz.", "2.75"), ("16 oz.", "4.50")),
            },
            {
                "name": "Homemade Cheddar Cheese Sauce",
                "display_order": 9,
                "variants": _sizes(("8 oz.", "2.75"), ("16 oz.", "4.50")),
            },
        ],
    },
]


# These entries are intentionally not inserted by the initial fixed-price seed.
# They require either clarification from the restaurant/source layout or a schema
# enhancement rather than guessed values.
SEED_REVIEW_NOTES = [
    {
        "entry": "Seafood > Lobster Roll (seasonal)",
        "reason": "Published price is 'market'; current MenuItemVariant.price requires a fixed positive NUMERIC value.",
    },
    {
        "entry": "Salads > Lobster Salad",
        "reason": "Published price is 'MP'; current MenuItemVariant.price requires a fixed positive NUMERIC value.",
    },
    {
        "entry": "Mac & Cheese Station > Cheeseburger",
        "reason": "Published page extraction associates Large $34.25 and X-Large $44.75 with this row in a way that appears structurally inconsistent with surrounding single-price items; verify before seeding.",
    },
    {
        "entry": "Side Orders",
        "reason": "The published section mixes one-, two-, and three-price rows under Small/Medium/Large headers, and text extraction does not reliably preserve blank columns. Verify size-to-price mappings before seeding this category.",
    },
    {
        "entry": "Soups (seasonal)",
        "reason": "The extracted row shows three prices ($4.65/$6.75/$12.65) but does not preserve all size headers reliably. Verify size labels before seeding.",
    },
    {
        "entry": "Pizza toppings / Salad toppers / sandwich add-ons / gluten-free upgrades / dipping sauces / dressing choices",
        "reason": "These are modifier-style offerings and should be seeded into GEO-20 modifier tables rather than flattened into MENU_DATA items.",
    },
]


# Modifier source data that can be translated into GEO-20 ModifierGroup /
# ModifierOption records in a follow-up pass. Prices are included only where the
# published page gives a clear single adjustment.
MODIFIER_SOURCE_DATA = {
    "pizza_toppings": [
        "Extra Cheese",
        "Mushroom",
        "Ham",
        "Broccoli",
        "Pesto",
        "Pepperoni",
        "Olives",
        "Bacon",
        "Ricotta",
        "Jalapeno Peppers",
        "Onion",
        "Eggplant",
        "Linguica",
        "Caramelized Onions",
        "Pepper",
        "Pineapple",
        "Hamburger",
        "Fresh Basil",
        "Spinach",
        "Artichoke",
        "Sausage",
        "Sliced Tomatoes",
        "Fresh Mozzarella",
        "Garlic",
        "Salami",
        "Anchovies",
        "Roasted Red Pepper",
        "Banana Peppers",
    ],
    "salad_toppers": [
        {"name": "Avocado", "price": "2.60"},
        {"name": "Walnuts", "price": "1.20"},
        {"name": "Dried Cranberries", "price": "1.00"},
        {"name": "Bacon", "price": "2.75"},
        {"name": "Feta", "price": "2.00"},
        {"name": "Pizza Cheese", "price": "2.00"},
        {"name": "Beets", "price": "2.00"},
        {"name": "Anchovies", "price": "2.60"},
        {"name": "Hard Boiled Egg", "price": "2.25"},
        {"name": "Fresh Mozzarella", "price": "2.50"},
        {"name": "Crumbled Blue Cheese", "price": "2.50"},
        {"name": "Goat Cheese", "price": "2.50"},
        {"name": "Jalapeno Peppers", "price": "1.25"},
        {"name": "Peppercinies", "price": "1.25"},
        {"name": "Banana Peppers", "price": "1.25"},
        {"name": "Roasted Red Peppers", "price": "1.25"},
        {"name": "Broccoli", "price": "2.50"},
    ],
    "dipping_sauces": [
        {"name": "Homemade Marinara", "price": "0.95"},
        {"name": "Homemade Buffalo Sauce", "price": "0.95"},
        {"name": "Homemade Alfredo Sauce", "price": "1.05"},
        {"name": "Pesto Sauce", "price": "1.05"},
        {"name": "Homemade Cheddar Cheese Sauce", "price": "1.05"},
        {"name": "Hot Honey", "price": "3.00"},
    ],
    "hot_sandwich_add_ons": {
        "Grilled Cheese": [
            {"name": "Add Ham", "price": "2.00"},
            {"name": "Add Tomato", "price": "1.00"},
            {"name": "Add Bacon", "price": "2.75"},
            {"name": "Add Avocado", "price": "2.75"},
        ],
        "Tuna Melt": [
            {"name": "Add Bacon", "price": "2.75"},
            {"name": "Add Avocado", "price": "2.75"},
        ],
    },
    "gluten_free_upgrades": [
        {
            "applies_to": "Georgio's Famous Hot Roast Beef",
            "name": "Gluten Free Roll",
            "price": "2.50",
        },
        {"applies_to": "Hot Sandwiches", "name": "Gluten Free Roll", "price": "2.50"},
        {"applies_to": "Hot Subs", "name": "Gluten Free Sub Roll", "price": "3.75"},
    ],
}
