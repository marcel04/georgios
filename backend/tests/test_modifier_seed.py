"""Exercise modifier seeding and item-detail serialization without PostgreSQL."""

from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    MenuCategory,
    MenuItem,
    ModifierGroup,
    ModifierOption,
    ModifierOptionPrice,
)
from app.seeds.menu import seed_menu
from app.seeds.menu_data import PIZZA_TOPPING_OPTIONS


@pytest.fixture
def seeded_db(menu_engine):
    with Session(menu_engine) as db:
        seed_menu(db)
        yield db


def find_item(db, category, name=None):
    statement = select(MenuItem).join(MenuCategory).where(MenuCategory.name == category)
    if name is not None:
        return db.scalars(statement.where(MenuItem.name == name)).one()
    return db.scalars(statement.order_by(MenuItem.display_order)).first()


def assert_prices(item, option, amount):
    assert len(option.prices) == len(item.variants)
    assert {price.menu_item_variant_id for price in option.prices} == {
        variant.id for variant in item.variants
    }
    assert {price.price_adjustment for price in option.prices} == {Decimal(amount)}
    assert all(price.menu_item_id == item.id for price in option.prices)
    assert option.menu_item_id == item.id


@pytest.mark.parametrize("count", [1, 2, 3, 4])
def test_pizza_included_toppings_have_explicit_free_prices(seeded_db, count):
    name = "1 Topping" if count == 1 else f"{count} Toppings"
    item = find_item(seeded_db, "Pizzas", name)
    assert len(item.modifier_groups) == 1
    group = item.modifier_groups[0]
    assert group.name == "Choose Toppings"
    assert group.is_active
    assert (group.min_selections, group.max_selections) == (count, count)
    options = sorted(group.options, key=lambda option: option.display_order)
    assert [(o.name, o.display_order) for o in options] == [
        (o["name"], o["display_order"]) for o in PIZZA_TOPPING_OPTIONS
    ]
    assert len(options) == 28
    assert "Pepperoni" in {o.name for o in options}
    assert {v.name for v in item.variants} == {"Small", "Large", "X-Large (Sicilian)"}
    for option in options:
        assert_prices(item, option, "0.00")


@pytest.mark.parametrize(
    "category,expected",
    [
        (
            "Pasta Dishes",
            {
                "Pasta Type": ["Spaghetti", "Ziti", "Cellentani"],
                "Sauce": ["Homemade Marinara", "Homemade Alfredo"],
            },
        ),
        (
            "Georgio's Club Sandwiches",
            {
                "Bread Type": ["White", "Wheat", "Marble Rye"],
                "Side Choice": [
                    "Fries",
                    "Coleslaw",
                    "Potato Salad",
                    "Tri-Colored Pasta Salad",
                ],
            },
        ),
    ],
)
def test_category_wide_required_choices(seeded_db, category, expected):
    items = seeded_db.scalars(
        select(MenuItem).join(MenuCategory).where(MenuCategory.name == category)
    ).all()
    assert items
    for item in items:
        groups = sorted(item.modifier_groups, key=lambda group: group.display_order)
        assert [group.name for group in groups] == list(expected)
        for group in groups:
            assert (group.min_selections, group.max_selections) == (1, 1)
            options = sorted(group.options, key=lambda option: option.display_order)
            assert [option.name for option in options] == expected[group.name]
            for option in options:
                assert_prices(item, option, "0.00")


@pytest.mark.parametrize(
    "name,prices",
    [
        (
            "Grilled Cheese",
            {"Ham": "2.00", "Tomato": "1.00", "Bacon": "2.75", "Avocado": "2.75"},
        ),
        ("Tuna Melt", {"Bacon": "2.75", "Avocado": "2.75"}),
    ],
)
def test_paid_sandwich_add_ons(seeded_db, name, prices):
    item = find_item(seeded_db, "Hot Sandwiches", name)
    group = next(g for g in item.modifier_groups if g.name == "Add-ons")
    assert group.name == "Add-ons"
    assert (group.min_selections, group.max_selections) == (0, len(prices))
    assert {option.name for option in group.options} == set(prices)
    for option in group.options:
        assert_prices(item, option, prices[option.name])


def test_salad_toppers_apply_to_every_salad(seeded_db):
    items = seeded_db.scalars(
        select(MenuItem).join(MenuCategory).where(MenuCategory.name == "Salads")
    ).all()
    assert items
    for item in items:
        group = next(g for g in item.modifier_groups if g.name == "Add Toppings")
        assert group.name == "Add Toppings"
        assert (group.min_selections, group.max_selections) == (0, 17)
        assert len(group.options) == 17
        options = {option.name: option for option in group.options}
        for name, amount in {
            "Avocado": "2.60",
            "Walnuts": "1.20",
            "Broccoli": "2.50",
        }.items():
            assert_prices(item, options[name], amount)


def test_reseed_preserves_modifier_counts_and_ownership(seeded_db):
    models = (ModifierGroup, ModifierOption, ModifierOptionPrice)
    counts = tuple(
        seeded_db.scalar(select(func.count()).select_from(m)) for m in models
    )
    assert all(count > 0 for count in counts)
    # Release loaded objects before replacement, just as a fresh CLI run would.
    seeded_db.expunge_all()
    seed_menu(seeded_db)
    assert (
        tuple(seeded_db.scalar(select(func.count()).select_from(m)) for m in models)
        == counts
    )
    for price in seeded_db.scalars(select(ModifierOptionPrice)):
        assert price.menu_item_id == price.modifier_option.menu_item_id
        assert price.menu_item_id == price.menu_item_variant.menu_item_id
    names = set(seeded_db.scalars(select(ModifierGroup.name)))
    assert names == {
        "Choose Toppings",
        "Pasta Type",
        "Sauce",
        "Bread Type",
        "Add-ons",
        "Add Toppings",
        "Dressing Type",
        "Side Choice",
    }
    assert not find_item(seeded_db, "Pizzas", "Cheese").modifier_groups


@pytest.mark.parametrize(
    "category,name,option_name,amount",
    [
        ("Pizzas", "2 Toppings", "Pepperoni", "0.00"),
        ("Hot Sandwiches", "Grilled Cheese", "Bacon", "2.75"),
    ],
)
def test_item_detail_returns_explicit_nested_prices(
    menu_api, category, name, option_name, amount
):
    client, engine = menu_api
    with Session(engine) as db:
        seed_menu(db)
        item_id = find_item(db, category, name).id
    response = client.get(f"/api/menu/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    group = next(
        g
        for g in data["modifier_groups"]
        if any(o["name"] == option_name for o in g["options"])
    )
    assert set(group) == {
        "id",
        "name",
        "min_selections",
        "max_selections",
        "display_order",
        "options",
    }
    option = next(o for o in group["options"] if o["name"] == option_name)
    assert set(option) == {"id", "name", "display_order", "prices"}
    assert {p["menu_item_variant_id"] for p in option["prices"]} == {
        v["id"] for v in data["variants"]
    }
    assert all(p["price_adjustment"] == amount for p in option["prices"])
    assert all(
        set(p) == {"menu_item_variant_id", "price_adjustment"} for p in option["prices"]
    )


def test_detail_filters_and_orders_groups_and_options(menu_api):
    client, engine = menu_api
    with Session(engine) as db:
        seed_menu(db)
        item = find_item(db, "Pasta Dishes")
        item_id = item.id
        groups = {group.name: group for group in item.modifier_groups}
        # Make display order disagree with insertion order without unique collisions.
        groups["Pasta Type"].display_order = 30
        groups["Sauce"].display_order = 20
        options = {option.name: option for option in groups["Pasta Type"].options}
        options["Spaghetti"].display_order = 30
        options["Ziti"].display_order = 20
        options["Cellentani"].is_available = False
        db.add(
            ModifierGroup(
                menu_item=item,
                name="Hidden",
                min_selections=0,
                max_selections=0,
                display_order=10,
                is_active=False,
            )
        )
        db.commit()
    response = client.get(f"/api/menu/items/{item_id}")
    assert response.status_code == 200
    groups = response.json()["modifier_groups"]
    assert [group["name"] for group in groups] == ["Sauce", "Pasta Type"]
    assert [option["name"] for option in groups[1]["options"]] == ["Ziti", "Spaghetti"]


def test_missing_price_fails_and_reset_can_be_rolled_back(seeded_db, monkeypatch):
    from app.seeds import menu

    original_id = find_item(seeded_db, "Pizzas", "2 Toppings").id
    monkeypatch.setattr(
        menu,
        "MENU_MODIFIER_DATA",
        [
            {
                "category_name": "Pizzas",
                "item_name": "2 Toppings",
                "name": "Invalid choice",
                "min_selections": 0,
                "max_selections": 1,
                "display_order": 1,
                "options": [{"name": "Missing price", "display_order": 1}],
            }
        ],
    )
    with pytest.raises(KeyError, match="price_adjustment"):
        seed_menu(seeded_db)
    seeded_db.rollback()

    # No intermediate commit: rollback restores the original menu and modifiers.
    item = find_item(seeded_db, "Pizzas", "2 Toppings")
    assert item.id == original_id
    assert [group.name for group in item.modifier_groups] == ["Choose Toppings"]
    assert len(item.modifier_groups[0].options) == 28


@pytest.mark.parametrize(
    "category,group_name,expected",
    [
        (
            "Hot Subs",
            "Bread Type",
            {"Standard Sub Roll": "0.00", "Gluten Free Sub Roll": "3.75"},
        ),
        (
            "Hot Sandwiches",
            "Bread Type",
            {"Standard Roll": "0.00", "Gluten Free Roll": "2.50"},
        ),
        (
            "Georgio's Famous Hot Roast Beef",
            "Bread Type",
            {"Standard Roll": "0.00", "Gluten Free Roll": "2.50"},
        ),
        (
            "Dinners",
            "Side Choice",
            {
                "French Fries": "0.00",
                "Rice": "0.00",
                "Onion Rings": "0.00",
                "Mashed Potatoes": "0.00",
                "Tuscan Vegetables": "0.00",
                "Curly Fries": "2.00",
                "Sweet Potato Waffle Fries": "2.00",
            },
        ),
        (
            "Salads",
            "Dressing Type",
            {
                name: "0.00"
                for name in [
                    "House",
                    "Italian",
                    "Caesar",
                    "Zinfandel Vinaigrette",
                    "Balsamic Vinaigrette",
                    "Ranch",
                    "Honey Mustard",
                    "Olive Oil & Vinegar",
                    "Blue Cheese",
                ]
            },
        ),
    ],
)
def test_remaining_category_choices(seeded_db, category, group_name, expected):
    items = seeded_db.scalars(
        select(MenuItem).join(MenuCategory).where(MenuCategory.name == category)
    ).all()
    assert items
    for item in items:
        group = next(g for g in item.modifier_groups if g.name == group_name)
        assert (group.min_selections, group.max_selections) == (1, 1)
        options = sorted(group.options, key=lambda o: o.display_order)
        assert [o.name for o in options] == list(expected)
        for option in options:
            assert_prices(item, option, expected[option.name])
        if category == "Salads":
            assert [
                (g.name, g.display_order)
                for g in sorted(item.modifier_groups, key=lambda g: g.display_order)
            ] == [("Dressing Type", 1), ("Add Toppings", 2)]


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Loaded Fries", [("Regular", "8.95")]),
        ("Hummus Sweet Potato", [("8 oz.", "4.65"), ("15 oz.", "8.95")]),
        ("Steak Fries", [("Small", "5.05"), ("Medium", "6.10"), ("Large", "7.45")]),
        ("Jalapeno Poppers", [("Small", "8.95"), ("Medium", "15.10")]),
        ("Cheese Fries", [("Small", "6.35"), ("Medium", "7.75"), ("Large", "10.95")]),
        ("Buffalo Cheese Fries", [("Regular", "11.10")]),
    ],
)
def test_side_order_variants(seeded_db, name, expected):
    item = find_item(seeded_db, "Side Orders", name)
    variants = sorted(item.variants, key=lambda v: v.display_order)
    assert [(v.name, v.price) for v in variants] == [
        (name, Decimal(price)) for name, price in expected
    ]
    assert [v.display_order for v in variants] == list(range(1, len(expected) + 1))


@pytest.mark.parametrize("name", ["Cheese Fries", "Buffalo Cheese Fries"])
def test_jalapenos_are_optional_add_ons_for_all_sizes(seeded_db, name):
    item = find_item(seeded_db, "Side Orders", name)
    (group,) = item.modifier_groups
    assert group.name == "Add-ons"
    assert (group.min_selections, group.max_selections) == (0, 1)
    (option,) = group.options
    assert option.name == "Jalapenos"
    assert_prices(item, option, "0.95")


def test_preserves_normal_items_and_clean_descriptions(seeded_db):
    sides = find_item(seeded_db, "Side Orders", "Chicken Fingers")
    wings = find_item(seeded_db, "Homemade Wings", "Chicken Fingers")
    assert sides.id != wings.id
    pizza = seeded_db.scalars(
        select(MenuItem).where(MenuItem.name == "Gluten Free Pizza")
    ).one()
    assert [v.price for v in pizza.variants] == [Decimal("18.65")]
    assert not pizza.modifier_groups
    for name in [
        "Homemade Marinara Sauce",
        "Homemade Alfredo Sauce",
        "Homemade Cheddar Cheese Sauce",
    ]:
        assert find_item(seeded_db, "Extras", name)
    expected = {
        "House Fries": "Crispy shoestring fries smothered with feta cheese and our homemade Greek dressing.",
        "Bang Bang Cauliflower": "Fresh cauliflower lightly battered and smothered in our sweet Asian chili sauce. Served with ranch dressing.",
        "Bang Bang Shrimp": "Fresh shrimp lightly battered and smothered in our sweet Asian chili sauce. Served with ranch dressing.",
        "Cheesy Sticks": "Served with marinara.",
        "Garlic Cheesy Sticks": "Served with marinara.",
        "Loaded Mashed Potatoes": "Crispy bacon covered with our homemade cheddar cheese sauce.",
        "Cheese Fries": "Crispy french fries smothered in our homemade cheddar cheese sauce.",
        "Buffalo Cheese Fries": "Crispy french fries tossed in our homemade buffalo sauce and homemade cheddar cheese sauce.",
    }
    for name, description in expected.items():
        assert find_item(seeded_db, "Side Orders", name).description == description
    assert not seeded_db.scalars(
        select(ModifierGroup).where(ModifierGroup.name == "Dipping Sauces")
    ).all()
    toppings = seeded_db.scalars(
        select(ModifierGroup).where(ModifierGroup.name == "Choose Toppings")
    ).all()
    assert len(toppings) == 4
    assert all(g.max_selections <= 4 for g in toppings)
