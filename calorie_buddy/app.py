from flask import Flask, render_template, request
import pandas as pd
import random

app = Flask(__name__)

# Load food data
df = pd.read_csv("calories.csv")

# Define the category mapping by subcategory
CATEGORY_MAP = {
    "Seafood Mix": [
        "Shellfish", "Crustaceans", "Fish", "Seafood"
    ],
    "Non-Vegetarian": [
        "Meat", "Poultry", "Sausages", "Bacon", "Beef", "Lamb"
    ],
    "Vegetarian": [
        "Dairy", "Cheese", "Eggs", "Vegetarian Meals"
    ],
    "Vegan": [
        "Fruits", "Vegetables", "Legumes", "Tofu", "Vegan Meals"
    ]
}

# Classify each food item
def classify_row(row):
    for category, subs in CATEGORY_MAP.items():
        if any(sub.lower() in row['Subcategory'].lower() for sub in subs):
            return category
    return None

df["Category"] = df.apply(classify_row, axis=1)
df = df[df["Category"].notnull()]

# Generate one combo under calorie limit
def generate_combo(category, target_calories):
    category_df = df[df["Category"] == category]
    subcategories = category_df["Subcategory"].unique()
    random.shuffle(subcategories)
    
    selected = []
    remaining_cal = target_calories

    for sub in subcategories:
        options = category_df[(category_df["Subcategory"] == sub) & (category_df["Calories"] <= remaining_cal)]
        if not options.empty:
            food = options.sample(1).iloc[0]
            selected.append(food)
            remaining_cal -= food["Calories"]
        if len(selected) == 4:
            break

    total_cal = sum(item["Calories"] for item in selected)
    return selected, total_cal

@app.route("/", methods=["GET", "POST"])
def index():
    meal_combinations = {}
    calorie_target = None

    if request.method == "POST":
        try:
            calorie_target = int(request.form["calorie_target"])
            for category in ["Vegetarian", "Non-Vegetarian", "Seafood Mix", "Vegan"]:
                combo, total = generate_combo(category, calorie_target)
                meal_combinations[category] = {
                    "meals": combo,
                    "total": total
                }
        except Exception as e:
            print("Error:", e)

    return render_template("index.html", meal_combinations=meal_combinations, calorie_target=calorie_target)

if __name__ == "__main__":
    app.run(debug=True)