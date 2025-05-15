from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from data_processor import load_and_process_data
from meal_generator import generate_meal_plans

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'calorie-buddy-flask-app-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calorie_buddy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Remove the custom JSON encoder approach and handle NumPy types directly in our code

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    meal_plans = db.relationship('MealPlan', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# MealPlan model to store saved and history meal plans
class MealPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False, default=datetime.now().strftime("%Y-%m-%d"))
    target_calories = db.Column(db.Integer, nullable=False)
    diet_type = db.Column(db.String(20), nullable=False)
    actual_calories = db.Column(db.Integer, nullable=False)
    foods = db.Column(db.Text, nullable=False)  # Stored as JSON string
    is_saved = db.Column(db.Boolean, default=False)  # False = history, True = saved

# Create tables in the database
with app.app_context():
    db.create_all()

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load food data at startup
food_data = load_and_process_data('calories.csv')

# Context processor to inject date into all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Routes
@app.route('/')
def home():
    """Home page route"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register route"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/meal_planner', methods=['GET', 'POST'])
@login_required
def meal_planner():
    """Meal planner route"""
    if request.method == 'POST':
        # Get form data
        target_calories = int(request.form.get('target_calories', 2000))
        min_calories = int(target_calories * 0.95)  # 5% below target
        max_calories = int(target_calories * 1.05)  # 5% above target
        
        # Generate meal plans
        meal_plans = generate_meal_plans(
            food_data, 
            target_calories=target_calories, 
            min_calories=min_calories, 
            max_calories=max_calories
        )
        
        # Convert to a format easier to use in templates with explicit type conversion
        formatted_plans = {}
        for diet_type, items in meal_plans.items():
            if not items:
                formatted_plans[diet_type] = {
                    'foods': [],
                    'total_calories': 0
                }
                continue
            
            # Convert NumPy types to Python native types
            formatted_items = []
            for item in items:
                formatted_item = {
                    'food': item['food'],
                    'serving': item['serving'],
                    'calories': int(item['calories']),  # Convert np.int64 to regular int
                    'subcategory': item['subcategory']
                }
                formatted_items.append(formatted_item)
                
            formatted_plans[diet_type] = {
                'foods': formatted_items,
                'total_calories': int(sum(item['calories'] for item in items))  # Convert sum to regular int
            }
            
            # Store in user's meal history
            foods_json = json.dumps([item['food'] for item in items])
            total_calories = formatted_plans[diet_type]['total_calories']
            
            meal_plan = MealPlan(
                user_id=current_user.id,
                date=datetime.now().strftime("%Y-%m-%d"),
                target_calories=target_calories,
                diet_type=diet_type,
                actual_calories=total_calories,
                foods=foods_json,
                is_saved=False
            )
            
            db.session.add(meal_plan)
        
        db.session.commit()
        
        # Store in session for the current request - with explicit type conversion
        # Use a new dict with primitive Python types for session storage
        session_plans = {}
        for diet_type, plan_data in formatted_plans.items():
            session_plans[diet_type] = {
                'foods': plan_data['foods'],
                'total_calories': plan_data['total_calories']
            }
            
        session['meal_plans'] = session_plans
        session['target_calories'] = int(target_calories)
        
        return render_template('meal_planner.html', meal_plans=formatted_plans, target_calories=target_calories)
    
    # Check if there are meal plans in session
    meal_plans = session.get('meal_plans', None)
    target_calories = session.get('target_calories', 2000)
    
    return render_template('meal_planner.html', meal_plans=meal_plans, target_calories=target_calories)

@app.route('/save_meal_plan', methods=['POST'])
@login_required
def save_meal_plan():
    """Save a meal plan to user's favorites"""
    diet_type = request.form.get('diet_type')
    target_calories = int(request.form.get('target_calories'))
    actual_calories = int(request.form.get('actual_calories'))
    foods_json = request.form.get('foods')
    
    # Create saved meal plan
    saved_plan = MealPlan(
        user_id=current_user.id,
        date=datetime.now().strftime("%Y-%m-%d"),
        target_calories=target_calories,
        diet_type=diet_type,
        actual_calories=actual_calories,
        foods=foods_json,
        is_saved=True
    )
    
    db.session.add(saved_plan)
    db.session.commit()
    
    flash(f'Saved {diet_type} meal plan successfully!', 'success')
    return redirect(url_for('meal_planner'))

@app.route('/analytics')
@login_required
def analytics():
    """Analytics route"""
    # Get ALL user's meal plans (both history and saved) to have more data for analytics
    meal_history = MealPlan.query.filter_by(user_id=current_user.id).order_by(MealPlan.date.desc()).all()
    
    if not meal_history:
        return render_template('analytics.html', has_data=False)
    
    # Process meal history for charts
    chart_data = []
    for entry in meal_history:
        # Safely convert values to integers, handling different data types
        try:
            # Handle binary representation of calories
            if isinstance(entry.target_calories, bytes):
                target = int.from_bytes(entry.target_calories, byteorder='little')
            else:
                target = int(entry.target_calories)
                
            if isinstance(entry.actual_calories, bytes):
                actual = int.from_bytes(entry.actual_calories, byteorder='little')
            else:
                actual = int(entry.actual_calories)
            
            # Sanity check for unreasonable values (data corruption)
            if target < 0 or target > 10000 or actual < 0 or actual > 10000:
                print(f"Skipping entry with unreasonable calorie values: Target={target}, Actual={actual}")
                continue
                
            difference = actual - target
            if target > 0:
                accuracy_pct = abs(difference) / target * 100
                accuracy = min(100, max(0, 100 - accuracy_pct))
            else:
                accuracy = 0
                
            chart_data.append({
                'Date': entry.date,
                'Diet Type': entry.diet_type,
                'Target': target,
                'Actual': actual,
                'Difference': difference,
                'Accuracy': accuracy
            })
        except Exception as e:
            print(f"Error processing meal plan data: {e}")
            print(f"Problematic entry: {entry.id}, Type: {entry.diet_type}, Target: {type(entry.target_calories)}, Actual: {type(entry.actual_calories)}")
    
    # If we don't have enough data after processing, show the no data message
    if len(chart_data) < 1:
        return render_template('analytics.html', has_data=False)
        
    df = pd.DataFrame(chart_data)
    
    # Create chart 1: Calories by Diet Type - with manual aggregation
    # Group by diet type and calculate mean of actual calories manually
    diet_type_calories = {}
    
    # Collect calorie values by diet type
    for item in chart_data:
        diet_type = item['Diet Type']
        calories = item['Actual']
        
        if diet_type not in diet_type_calories:
            diet_type_calories[diet_type] = []
        
        diet_type_calories[diet_type].append(calories)
    
    # Calculate average calories for each diet type
    avg_calories_data = []
    for diet_type, calories_list in diet_type_calories.items():
        if calories_list:  # Check if we have data for this diet type
            avg_calories = sum(calories_list) / len(calories_list)
            avg_calories_data.append({
                'Diet Type': diet_type, 
                'Average Calories': int(avg_calories)
            })
    
    # Sort by diet type for consistent ordering
    avg_calories_data = sorted(avg_calories_data, key=lambda x: x['Diet Type'])
    
    # Create the figure using plain lists instead of DataFrame
    diet_types = [item['Diet Type'] for item in avg_calories_data]
    avg_calories = [item['Average Calories'] for item in avg_calories_data]
    
    # Create a simple bar chart using plotly graph objects directly
    fig1 = go.Figure()
    
    # Add bars with colors
    colors = px.colors.qualitative.Plotly  # Standard color sequence
    
    for i, (diet, calories) in enumerate(zip(diet_types, avg_calories)):
        color = colors[i % len(colors)]
        fig1.add_trace(go.Bar(
            x=[diet],
            y=[calories],
            name=diet,
            marker_color=color,
            text=[calories],
            textposition='outside'
        ))
    
    # Update layout
    fig1.update_layout(
        title='Average Calories by Diet Type',
        xaxis_title='Diet Type',
        yaxis_title='Average Calories',
        height=400,
        showlegend=True
    )
    
    # Create chart 2: Target vs Actual - using direct plotting approach
    # First gather and calculate the data manually
    target_actual_data = {}
    
    for item in chart_data:
        diet_type = item['Diet Type']
        if diet_type not in target_actual_data:
            target_actual_data[diet_type] = {'Target': [], 'Actual': [], 'Accuracy': []}
            
        target_actual_data[diet_type]['Target'].append(item['Target'])
        target_actual_data[diet_type]['Actual'].append(item['Actual'])
        target_actual_data[diet_type]['Accuracy'].append(item['Accuracy'])
    
    # Calculate averages
    diet_types = []
    avg_targets = []
    avg_actuals = []
    avg_accuracies = []
    
    for diet_type, values in sorted(target_actual_data.items()):
        if values['Target'] and values['Actual']:  # Only process if we have data
            diet_types.append(diet_type)
            avg_targets.append(int(sum(values['Target']) / len(values['Target'])))
            avg_actuals.append(int(sum(values['Actual']) / len(values['Actual'])))
            avg_accuracies.append(int(sum(values['Accuracy']) / len(values['Accuracy'])))
    
    # Create the subplot figure
    fig2 = make_subplots(
        rows=1, cols=2, 
        subplot_titles=('Target vs Actual Calories', 'Accuracy by Diet Type'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    # Add target vs actual bars with text labels
    fig2.add_trace(
        go.Bar(
            name='Target', 
            x=diet_types, 
            y=avg_targets, 
            marker_color='red',
            text=avg_targets,
            textposition='outside'
        ),
        row=1, col=1
    )
    
    fig2.add_trace(
        go.Bar(
            name='Actual', 
            x=diet_types, 
            y=avg_actuals, 
            marker_color='blue',
            text=avg_actuals,
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Add accuracy bars with text labels
    fig2.add_trace(
        go.Bar(
            name='Accuracy (%)', 
            x=diet_types, 
            y=avg_accuracies, 
            marker_color='green',
            text=[f"{acc}%" for acc in avg_accuracies],
            textposition='outside'
        ),
        row=1, col=2
    )
    
    # Add a horizontal line at 90% accuracy
    if diet_types:  # Only add line if we have data points
        fig2.add_shape(
            type='line',
            x0=-0.5,
            x1=len(diet_types)-0.5,
            y0=90,
            y1=90,
            line=dict(color='red', width=2, dash='dash'),
            row=1, col=2
        )
    
    # Update layout
    fig2.update_layout(
        height=400, 
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Adjust y-axis range to make room for labels
    fig2.update_yaxes(range=[0, max(avg_targets + avg_actuals) * 1.15], row=1, col=1)
    fig2.update_yaxes(range=[0, 110], row=1, col=2)
    
    # Create chart 3: Diet Type Distribution
    # Count occurrences of each diet type manually
    diet_type_counts = {}
    for item in chart_data:
        diet_type = item['Diet Type']
        if diet_type not in diet_type_counts:
            diet_type_counts[diet_type] = 0
        diet_type_counts[diet_type] += 1
    
    # Calculate percentages
    total_count = sum(diet_type_counts.values())
    labels = []
    values = []
    percentages = []
    
    for diet_type, count in sorted(diet_type_counts.items()):
        percentage = (count / total_count * 100) if total_count > 0 else 0
        labels.append(diet_type)
        values.append(count)
        percentages.append(round(percentage, 1))
    
    # Create pie chart using direct Plotly method
    fig3 = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,  # Creates a donut chart for better appearance
        textinfo='label+percent',
        hoverinfo='label+value+percent',
        textposition='outside',
        pull=[0.05] * len(labels),  # Slightly pull all slices for better visualization
        marker=dict(
            colors=px.colors.qualitative.Plotly[:len(labels)],
            line=dict(color='white', width=2)
        )
    )])
    
    fig3.update_layout(
        title='Diet Type Distribution',
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5)
    )
    
    # Convert figures to JSON for the template
    chart1_json = pio.to_json(fig1)
    chart2_json = pio.to_json(fig2)
    chart3_json = pio.to_json(fig3)
    
    # Get summary statistics manually without relying on pandas aggregation
    stats_data = {}
    for item in chart_data:
        diet_type = item['Diet Type']
        actual = item['Actual']
        
        if diet_type not in stats_data:
            stats_data[diet_type] = {'values': []}
        
        stats_data[diet_type]['values'].append(actual)
    
    stats = []
    for diet_type, data in sorted(stats_data.items()):
        values = data['values']
        if values:
            avg = int(round(sum(values) / len(values)))
            min_val = int(min(values))
            max_val = int(max(values))
            
            stats.append({
                'Diet Type': diet_type,
                'Average': avg,
                'Minimum': min_val,
                'Maximum': max_val
            })
    
    # Get most popular diet type
    most_popular_diet = None
    max_count = 0
    diet_counts = {}
    
    # Count diet type occurrences
    for item in chart_data:
        diet_type = item['Diet Type']
        if diet_type not in diet_counts:
            diet_counts[diet_type] = 0
        diet_counts[diet_type] += 1
    
    # Find the most popular one
    for diet_type, count in diet_counts.items():
        if count > max_count:
            max_count = count
            most_popular_diet = diet_type
    
    # Calculate total and percentage
    total_count = sum(diet_counts.values())
    
    if most_popular_diet and total_count > 0:
        percentage = (diet_counts[most_popular_diet] / total_count) * 100
        most_popular = {
            'Diet Type': most_popular_diet,
            'Count': diet_counts[most_popular_diet],
            'Percentage': round(percentage, 1)
        }
    else:
        most_popular = {'Diet Type': 'None', 'Count': 0, 'Percentage': 0}
    
    return render_template(
        'analytics.html', 
        has_data=True,
        chart1_json=chart1_json,
        chart2_json=chart2_json,
        chart3_json=chart3_json,
        stats=stats,
        most_popular=most_popular
    )

@app.route('/profile')
@login_required
def profile():
    """Profile page route"""
    # Get user's saved meal plans
    saved_plans = MealPlan.query.filter_by(user_id=current_user.id, is_saved=True).order_by(MealPlan.date.desc()).all()
    
    # Format saved plans for display
    formatted_saved_plans = []
    for plan in saved_plans:
        try:
            # Safe JSON parsing with error handling
            if isinstance(plan.foods, bytes):
                # Handle case where foods is stored as binary
                foods_str = plan.foods.decode('utf-8', errors='replace')
            else:
                foods_str = plan.foods
                
            # Check if the string starts with a quote (proper JSON)
            if foods_str and foods_str[0] == '"':
                # Handle double-encoded JSON (string within string)
                foods_str = foods_str.strip('"')
                
            # Try to parse JSON, with fallback to empty list
            try:
                foods = json.loads(foods_str)
            except:
                print(f"Failed to parse foods JSON for plan {plan.id}: {foods_str}")
                foods = []
            
            # Handle correct data types for calories
            if isinstance(plan.target_calories, bytes):
                target_calories = int.from_bytes(plan.target_calories, byteorder='little')
            else:
                target_calories = int(plan.target_calories)
                
            if isinstance(plan.actual_calories, bytes):
                actual_calories = int.from_bytes(plan.actual_calories, byteorder='little')
            else:
                actual_calories = int(plan.actual_calories)
            
            formatted_saved_plans.append({
                'id': plan.id,
                'date': plan.date,
                'diet_type': plan.diet_type,
                'target_calories': target_calories,
                'actual_calories': actual_calories,
                'foods': foods
            })
        except Exception as e:
            print(f"Error processing meal plan {plan.id}: {e}")
            # Skip this plan if we can't process it
            continue
    
    return render_template('profile.html', saved_plans=formatted_saved_plans)

@app.route('/delete_meal_plan/<int:plan_id>', methods=['POST'])
@login_required
def delete_meal_plan(plan_id):
    """Delete a saved meal plan"""
    plan = MealPlan.query.get_or_404(plan_id)
    
    # Check if the plan belongs to the current user
    if plan.user_id != current_user.id:
        flash('Not authorized to delete this meal plan', 'danger')
        return redirect(url_for('profile'))
    
    db.session.delete(plan)
    db.session.commit()
    
    flash('Meal plan deleted successfully', 'success')
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)