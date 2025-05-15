import json
from datetime import datetime
from app import db, User, MealPlan


def register_user(username: str, password: str, email: str):
    """Register a new user in the database."""
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return False, "Username already exists"

    # Create and save new user
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return True, "Registration successful"


def authenticate_user(username: str, password: str):
    """Authenticate a user, returning the User object on success."""
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return None, "Invalid username or password"
    return user, "Login successful"


def get_user_data(username: str) -> dict:
    """Retrieve user info plus their meal history and saved plans."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return {}

    # Helper to serialize a MealPlan
    def _serialize(plan: MealPlan) -> dict:
        # Parse JSON foods field
        try:
            foods = json.loads(plan.foods)
        except Exception:
            foods = []

        return {
            'id': plan.id,
            'date': plan.date,
            'diet_type': plan.diet_type,
            'target_calories': plan.target_calories,
            'actual_calories': plan.actual_calories,
            'foods': foods,
            'is_saved': plan.is_saved
        }

    history = MealPlan.query.filter_by(user_id=user.id, is_saved=False).order_by(MealPlan.date.desc()).all()
    saved = MealPlan.query.filter_by(user_id=user.id, is_saved=True).order_by(MealPlan.date.desc()).all()

    return {
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at,
        'meal_history': [_serialize(p) for p in history],
        'saved_plans': [_serialize(p) for p in saved]
    }


def save_meal_plan(username: str, plan_data: dict, is_saved: bool = True) -> bool:
    """Save a new meal plan for the given user."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return False

    foods_json = json.dumps(plan_data.get('foods', []))
    plan = MealPlan(
        user_id=user.id,
        date=plan_data.get('date', datetime.now().strftime("%Y-%m-%d")),
        target_calories=plan_data.get('target_calories', 0),
        diet_type=plan_data.get('diet_type', ''),
        actual_calories=plan_data.get('actual_calories', 0),
        foods=foods_json,
        is_saved=is_saved
    )
    db.session.add(plan)
    db.session.commit()
    return True


def update_meal_history(username: str, new_history: list[dict]) -> bool:
    """Replace all non-saved meal history entries for a user with new data."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return False

    # Delete existing non-saved history
    MealPlan.query.filter_by(user_id=user.id, is_saved=False).delete()

    # Insert new history entries
    for entry in new_history:
        foods_json = json.dumps(entry.get('foods', []))
        plan = MealPlan(
            user_id=user.id,
            date=entry.get('date', datetime.now().strftime("%Y-%m-%d")),
            target_calories=entry.get('target_calories', 0),
            diet_type=entry.get('diet_type', ''),
            actual_calories=entry.get('actual_calories', 0),
            foods=foods_json,
            is_saved=False
        )
        db.session.add(plan)

    db.session.commit()
    return True
