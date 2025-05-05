import pandas as pd
import numpy as np
import re

def load_and_process_data(file_path):
    """
    Load and process the CSV data file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Processed food data with dietary category information
    """
    # Load data
    try:
        food_data = pd.read_csv(file_path)
    except Exception as e:
        raise Exception(f"Error loading CSV file: {e}")
    
    # Add dietary category information
    food_data['is_vegetarian'] = food_data.apply(categorize_vegetarian, axis=1)
    food_data['is_vegan'] = food_data.apply(categorize_vegan, axis=1)
    food_data['is_seafood'] = food_data.apply(categorize_seafood, axis=1)
    food_data['is_non_vegetarian'] = food_data.apply(categorize_non_vegetarian, axis=1)
    
    # Convert calories to numeric
    food_data['calories'] = food_data['Calories'].apply(lambda x: int(x.split()[0]) if pd.notna(x) else 0)
    
    # Rename columns for consistency
    food_data = food_data.rename(columns={
        'Subcategory': 'subcategory',
        'Food': 'food',
        'Serving': 'serving'
    })
    
    return food_data

def categorize_vegetarian(row):
    """
    Check if a food item is vegetarian.
    This function ensures strict exclusion of all meat products.
    """
    # Categories that are non-vegetarian
    non_veg_categories = [
        'Meat', 'Beef & Veal', 'Pork & Ham', 'Poultry', 'Game Meats',
        'Sausages & Cold Cuts', 'Fish & Seafood', 'Meat & Poultry',
        'Processed Meats'
    ]
    
    # Comprehensive list of foods that contain meat
    meat_keywords = [
        # Red meat
        'beef', 'pork', 'lamb', 'mutton', 'veal', 'goat', 'venison', 'deer', 
        'elk', 'buffalo', 'bison', 'rabbit', 'horse', 'boar', 'ham', 'bacon',
        
        # Processed meats
        'sausage', 'salami', 'pepperoni', 'prosciutto', 'bologna', 'pastrami',
        'corned beef', 'hotdog', 'hot dog', 'bratwurst', 'chorizo', 'steak',
        'jerky', 'meatloaf', 'meatball', 'hamburger', 'burger', 'pate',
        
        # Poultry
        'chicken', 'turkey', 'duck', 'goose', 'quail', 'pheasant', 'pigeon',
        'guinea fowl', 'ostrich', 'emu', 'drumstick', 'wing', 'poultry',
        
        # Fish
        'fish', 'salmon', 'tuna', 'tilapia', 'sardine', 'anchovy', 'mackerel',
        'cod', 'halibut', 'trout', 'snapper', 'haddock', 'catfish', 'bass',
        'herring', 'swordfish', 'mahi-mahi', 'flounder', 'perch', 'sole',
        
        # Seafood
        'shrimp', 'prawn', 'lobster', 'crab', 'oyster', 'mussel', 'clam',
        'scallop', 'squid', 'octopus', 'calamari', 'crawfish', 'shellfish',
        'seafood',
        
        # Other meats
        'offal', 'liver', 'kidney', 'heart', 'tongue', 'brain', 'tripe',
        'sweetbread', 'bone marrow', 'foie gras',
        
        # Generic terms
        'meat', 'carne', 'flesh', 'animal', 'bbq', 'barbecue'
    ]
    
    # Check if the subcategory is clearly non-vegetarian
    if row['Subcategory'] in non_veg_categories:
        return False
    
    # Check for meat keywords in the food name
    food_name = str(row['Food']).lower()
    
    # First check exact matches
    for keyword in meat_keywords:
        if keyword in food_name.split():  # Check for full word matches
            return False
    
    # Then check for substring matches
    for keyword in meat_keywords:
        if len(keyword) > 3 and keyword in food_name:  # Only check longer keywords as substrings
            return False
    
    # Special cases and dishes that typically contain meat
    non_vegetarian_dishes = [
        'bolognese', 'carbonara', 'meatlovers', 'meat lovers', 'pepperoni',
        'al pastor', 'carnitas', 'carnivore', 'hunters', 'cacciatore', 
        'barbacoa', 'birria', 'cottage pie', 'shepherd', 'meatball',
        'beef wellington', 'stroganoff', 'schnitzel', 'gyro', 'shawarma', 
        'kebab', 'meatloaf', 'cheeseburger', 'hamburger', 'slider',
        'salisbury', 'surf and turf'
    ]
    
    for dish in non_vegetarian_dishes:
        if dish in food_name:
            return False
    
    # Special case for pizza (assume vegetarian unless it has meat keywords)
    if 'pizza' in food_name or row['Subcategory'] == 'Pizza':
        for keyword in ['pepperoni', 'sausage', 'meat lover', 'supreme', 'ham', 
                        'bacon', 'prosciutto', 'seafood', 'anchovy', 'hawaiian']:
            if keyword in food_name:
                return False
    
    # Some other food products that might contain animal-derived ingredients
    # but are still considered vegetarian (contain dairy/eggs)
    return True

def categorize_vegan(row):
    """
    Check if a food item is vegan based on manually verified categories and ingredients.
    This function implements stricter rules for vegan classification.
    """
    # First check if it's vegetarian
    if not categorize_vegetarian(row):
        return False
    
    # Explicitly vegan-friendly categories
    vegan_categories = [
        'Fruit', 
        'Vegetables & Legumes',
        'Nuts & Seeds'
    ]
    
    # Non-vegan categories (contain animal products or may have animal derivatives)
    non_vegan_categories = [
        'Dairy', 'Eggs', 'Milk & Yogurt', 'Cheese', 'Milk',
        'Ice Cream & Desserts', 'Pastry', 'Desserts', 'Sweets',
        'Snacks', 'Chocolate', 'Cake', 'Cookie', 'Biscuit',
        'Breakfast Cereals', 'Pie'
    ]
    
    # If the food is in an explicitly vegan category, it's likely vegan
    if row['Subcategory'] in vegan_categories:
        # But still check for specific non-vegan ingredients in these categories
        food_name = str(row['Food']).lower()
        
        # Some processed foods in these categories might contain animal products
        potentially_non_vegan = [
            'honey', 'butter', 'cheese', 'creamy', 'creamed'
        ]
        
        for keyword in potentially_non_vegan:
            if keyword in food_name:
                return False
                
        return True
    
    # If the food is in a non-vegan category, it's definitely not vegan
    if row['Subcategory'] in non_vegan_categories:
        return False
    
    # Additional non-vegan ingredients to check in other categories
    non_vegan_keywords = [
        'milk', 'cheese', 'cream', 'yogurt', 'butter', 'ghee', 'egg', 
        'honey', 'dairy', 'whey', 'casein', 'lactose', 'mozzarella',
        'parmesan', 'cheddar', 'ricotta', 'pizza', 'mayo', 'mayonnaise',
        'custard', 'pudding', 'ice cream', 'gelato', 'frosting',
        'chocolate', 'cake', 'cookie', 'cheesecake', 'pancake', 'waffle',
        'brioche', 'croissant', 'pastry', 'danish', 'milk chocolate'
    ]
    
    # Check for non-vegan keywords in the food name
    food_name = str(row['Food']).lower()
    for keyword in non_vegan_keywords:
        if keyword in food_name:
            return False
            
    # Explicitly known vegan foods from other categories
    vegan_foods = [
        'bread', 'whole wheat bread', 'whole grain bread', 'pita', 'pasta', 
        'rice', 'brown rice', 'white rice', 'noodles', 'cereal', 'oatmeal',
        'quinoa', 'couscous', 'barley', 'bulgur', 'farro', 'millet',
        'tempeh', 'tofu', 'seitan', 'hummus', 'tahini', 'falafel',
        'tabbouleh', 'sorbet', 'maple syrup', 'jam', 'jelly', 'marmalade',
        'peanut butter', 'almond butter', 'cashew butter', 'olive oil',
        'coconut oil', 'vegetable oil', 'canola oil', 'sunflower oil',
        'dark chocolate', 'soy milk', 'almond milk', 'oat milk', 'rice milk',
        'coconut milk', 'soy yogurt', 'coconut yogurt'
    ]
    
    # Check if it's an explicitly known vegan food
    for vegan_food in vegan_foods:
        if vegan_food in food_name:
            return True
    
    # For remaining foods, we'll be conservative and assume they're not vegan
    # unless they're fruits, vegetables, nuts, seeds, or legumes
    return False

def categorize_seafood(row):
    """Check if a food item is seafood"""
    seafood_categories = ['Fish & Seafood']
    seafood_keywords = [
        'fish', 'salmon', 'tuna', 'tilapia', 'sardine', 'herring', 'anchovy',
        'mackerel', 'cod', 'halibut', 'trout', 'snapper', 'shrimp', 'prawn',
        'lobster', 'crab', 'oyster', 'mussel', 'clam', 'scallop', 'squid',
        'octopus', 'calamari', 'seafood'
    ]
    
    # Check if the subcategory is seafood
    if row['Subcategory'] in seafood_categories:
        return True
    
    # Check for seafood keywords in the food name
    food_name = str(row['Food']).lower()
    for keyword in seafood_keywords:
        if keyword in food_name:
            return True
    
    return False

def categorize_non_vegetarian(row):
    """Check if a food item is non-vegetarian (contains meat but not seafood)"""
    # If it's vegetarian or seafood, it's not non-vegetarian
    if categorize_vegetarian(row) or categorize_seafood(row):
        return False
    
    meat_categories = [
        'Meat', 'Beef & Veal', 'Pork & Ham', 'Poultry', 'Game Meats',
        'Sausages & Cold Cuts'
    ]
    
    meat_keywords = [
        'beef', 'pork', 'chicken', 'turkey', 'duck', 'goose', 'lamb', 'mutton',
        'veal', 'ham', 'bacon', 'sausage', 'steak', 'ribs', 'venison', 'deer', 
        'elk', 'buffalo', 'bison', 'pepperoni', 'salami', 'prosciutto'
    ]
    
    # Check if the subcategory is meat
    if row['Subcategory'] in meat_categories:
        return True
    
    # Check for meat keywords in the food name
    food_name = str(row['Food']).lower()
    for keyword in meat_keywords:
        if keyword in food_name:
            return True
    
    return False
