from flask import Flask, render_template, request
from meal_generator import generate_meal_plans
from data_processor import load_and_process_data

app = Flask(__name__)

# Load food data once at startup
try:
    food_data = load_and_process_data("calories.csv")
except Exception as e:
    food_data = None
    print(f"Error loading data: {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    meal_plans = None
    target_calories = 2000
    error = None

    if request.method == "POST":
        try:
            target_calories = int(request.form["calories"])
            min_calories = int(target_calories * 0.9)
            max_calories = int(target_calories * 1.1)

            meal_plans = generate_meal_plans(
                food_data,
                target_calories=target_calories,
                min_calories=min_calories,
                max_calories=max_calories
            )
        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        meal_plans=meal_plans,
        target_calories=target_calories,
        error=error
    )

if __name__ == "__main__":
    app.run(debug=True,port = 5001)