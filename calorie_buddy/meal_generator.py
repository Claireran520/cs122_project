import random
import pandas as pd
import numpy as np

def generate_meal_plans(food_data, target_calories, min_calories, max_calories):
    """
    Generate four meal plans based on dietary preferences.
    
    Args:
        food_data (pd.DataFrame): Processed food data
        target_calories (int): Target calories for each meal plan
        min_calories (int): Minimum calories for each meal plan
        max_calories (int): Maximum calories for each meal plan
        
    Returns:
        dict: Four meal plans (Vegetarian, Non-Vegetarian, Seafood Mix, Vegan)
    """
    # Initialize meal plans
    meal_plans = {
        "Vegetarian": [],
        "Non-Vegetarian": [],
        "Seafood Mix": [],
        "Vegan": []
    }
    
    # Filter data for each dietary preference
    vegetarian_foods = food_data[food_data['is_vegetarian']].copy()
    non_vegetarian_foods = food_data[food_data['is_non_vegetarian']].copy()
    seafood_foods = food_data[food_data['is_seafood']].copy()
    vegan_foods = food_data[food_data['is_vegan']].copy()
    
    # For non-vegetarian and seafood plans, include vegetarian options too
    vegetarian_base = vegetarian_foods[~vegetarian_foods['is_vegan']].copy()  # Vegetarian but not vegan
    
    # Set the acceptable calorie tolerance (how close we want to be to target)
    # This represents 5% deviation from target in either direction
    tolerance = 0.05
    max_attempts = 5  # Try up to 5 times to get a better plan
    
    # Generate multiple vegetarian plans and pick the best one
    best_vegetarian_plan = []
    best_vegetarian_diff = float('inf')
    
    for _ in range(max_attempts):
        plan = generate_balanced_meal_plan(
            vegetarian_foods, 
            target_calories, 
            min_calories, 
            max_calories
        )
        
        if plan:
            total_cals = sum(item['calories'] for item in plan)
            diff = abs(total_cals - target_calories)
            
            if diff < best_vegetarian_diff:
                best_vegetarian_diff = diff
                best_vegetarian_plan = plan
                
                # If we're within tolerance, stop trying
                if diff <= target_calories * tolerance:
                    break
    
    # Generate multiple non-vegetarian plans and pick the best one
    best_non_veg_plan = []
    best_non_veg_diff = float('inf')
    
    for _ in range(max_attempts):
        plan = generate_balanced_meal_plan(
            pd.concat([non_vegetarian_foods, vegetarian_base.sample(frac=0.7)]), 
            target_calories, 
            min_calories, 
            max_calories,
            meat_ratio=0.4  # 40% of calories from meat
        )
        
        if plan:
            total_cals = sum(item['calories'] for item in plan)
            diff = abs(total_cals - target_calories)
            
            if diff < best_non_veg_diff:
                best_non_veg_diff = diff
                best_non_veg_plan = plan
                
                if diff <= target_calories * tolerance:
                    break
    
    # Generate multiple seafood plans and pick the best one
    best_seafood_plan = []
    best_seafood_diff = float('inf')
    
    for _ in range(max_attempts):
        plan = generate_balanced_meal_plan(
            pd.concat([seafood_foods, vegetarian_base.sample(frac=0.7)]), 
            target_calories, 
            min_calories, 
            max_calories,
            meat_ratio=0.35  # 35% of calories from seafood
        )
        
        if plan:
            total_cals = sum(item['calories'] for item in plan)
            diff = abs(total_cals - target_calories)
            
            if diff < best_seafood_diff:
                best_seafood_diff = diff
                best_seafood_plan = plan
                
                if diff <= target_calories * tolerance:
                    break
    
    # Generate multiple vegan plans and pick the best one
    best_vegan_plan = []
    best_vegan_diff = float('inf')
    
    for _ in range(max_attempts):
        plan = generate_balanced_meal_plan(
            vegan_foods, 
            target_calories, 
            min_calories, 
            max_calories
        )
        
        if plan:
            total_cals = sum(item['calories'] for item in plan)
            diff = abs(total_cals - target_calories)
            
            if diff < best_vegan_diff:
                best_vegan_diff = diff
                best_vegan_plan = plan
                
                if diff <= target_calories * tolerance:
                    break
    
    # Update meal plans with the best ones found
    meal_plans["Vegetarian"] = best_vegetarian_plan
    meal_plans["Non-Vegetarian"] = best_non_veg_plan
    meal_plans["Seafood Mix"] = best_seafood_plan
    meal_plans["Vegan"] = best_vegan_plan
    
    return meal_plans

def generate_balanced_meal_plan(foods_df, target_calories, min_calories, max_calories, meat_ratio=0.0):
    """
    Generate a balanced meal plan from the given food options.
    
    Args:
        foods_df (pd.DataFrame): Foods to choose from
        target_calories (int): Target calories for the meal plan
        min_calories (int): Minimum calories for the meal plan (not used in new algorithm)
        max_calories (int): Maximum calories for the meal plan (not used in new algorithm)
        meat_ratio (float): Ratio of calories that should come from meat/seafood
        
    Returns:
        list: Selected food items for the meal plan
    """
    if foods_df.empty:
        return []
    
    # Ensure we have a variety of subcategories
    subcategories = foods_df['subcategory'].unique()
    
    # If fewer than 3 subcategories available, return empty plan
    if len(subcategories) < 3:
        return []
    
    # Initialize meal plan
    meal_plan = []
    remaining_calories = target_calories  # Start with full target calories
    used_subcategories = set()
    
    # Special handling for non-vegetarian/seafood meal plans
    if meat_ratio > 0:
        # Identify meat/seafood items
        if 'is_seafood' in foods_df.columns and foods_df['is_seafood'].any():
            meat_items = foods_df[foods_df['is_seafood']].copy()
        else:
            meat_items = foods_df[foods_df['is_non_vegetarian']].copy()
        
        # Non-meat items
        non_meat_items = foods_df[~foods_df.index.isin(meat_items.index)].copy()
        
        # Calculate target calories for meat/seafood
        meat_target_calories = int(target_calories * meat_ratio)
        
        # Get unique subcategories for meat items
        meat_subcategories = meat_items['subcategory'].unique()
        
        # Ensure we choose from different meat subcategories if possible
        if len(meat_subcategories) >= 2:
            chosen_meat_subcats = random.sample(list(meat_subcategories), min(2, len(meat_subcategories)))
            meat_items_filtered = meat_items[meat_items['subcategory'].isin(chosen_meat_subcats)]
            
            if not meat_items_filtered.empty:
                meat_items = meat_items_filtered
        
        # Choose meat items that together approach the meat target calories
        remaining_meat_calories = meat_target_calories
        meat_count = 0
        max_meat_items = 2  # Limit to 2 meat items
        
        # Filter for reasonable meat items (not too high in calories)
        reasonable_meat_items = meat_items[meat_items['calories'] < (meat_target_calories * 0.7)].copy()
        if reasonable_meat_items.empty:
            reasonable_meat_items = meat_items.copy()
        
        while remaining_meat_calories > 0 and meat_count < max_meat_items:
            # Find a meat item close to remaining calories
            suitable_items = reasonable_meat_items[reasonable_meat_items['calories'] <= remaining_meat_calories]
            
            if suitable_items.empty:
                # If no items fit, take the one with lowest calories
                suitable_items = reasonable_meat_items.sort_values('calories').head(5)
            
            # Exclude already selected foods
            suitable_items = suitable_items[~suitable_items['food'].isin([item['food'] for item in meal_plan])]
            
            if suitable_items.empty:
                break
                
            # Select item
            selected_food = suitable_items.sample(1).iloc[0]
            
            # Add to meal plan
            meal_plan.append({
                'subcategory': selected_food['subcategory'],
                'food': selected_food['food'],
                'serving': selected_food['serving'],
                'calories': selected_food['calories']
            })
            
            # Update tracking variables
            remaining_meat_calories -= selected_food['calories']
            remaining_calories -= selected_food['calories']
            used_subcategories.add(selected_food['subcategory'])
            meat_count += 1
        
        # Now add non-meat items to complete the meal plan
        available_subcats = [subcat for subcat in non_meat_items['subcategory'].unique() 
                            if subcat not in used_subcategories]
        
        # Try to include different subcategories
        if len(available_subcats) >= 2:
            chosen_subcats = random.sample(available_subcats, min(2, len(available_subcats)))
            non_meat_filtered = non_meat_items[non_meat_items['subcategory'].isin(chosen_subcats)].copy()
            
            if not non_meat_filtered.empty:
                non_meat_items_to_use = non_meat_filtered
            else:
                non_meat_items_to_use = non_meat_items
        else:
            non_meat_items_to_use = non_meat_items
        
        # Choose non-meat items to complete the meal
        max_total_items = 4  # Maximum items in final meal plan
        while len(meal_plan) < max_total_items and remaining_calories > 0:
            # Find items close to the remaining calories
            suitable_items = non_meat_items_to_use[non_meat_items_to_use['calories'] <= remaining_calories]
            
            if suitable_items.empty:
                # If no items fit, take ones with lowest calories
                suitable_items = non_meat_items_to_use.sort_values('calories').head(5)
            
            # Exclude already selected foods and prefer unused subcategories
            unused_subcat_items = suitable_items[
                (~suitable_items['food'].isin([item['food'] for item in meal_plan])) &
                (~suitable_items['subcategory'].isin(used_subcategories))
            ]
            
            if unused_subcat_items.empty:
                # If no unused subcategories, just exclude selected foods
                unused_subcat_items = suitable_items[
                    ~suitable_items['food'].isin([item['food'] for item in meal_plan])
                ]
            
            if unused_subcat_items.empty:
                break
                
            # Select item that best matches remaining calories
            unused_subcat_items['calorie_diff'] = abs(unused_subcat_items['calories'] - remaining_calories/2)
            selected_food = unused_subcat_items.sort_values('calorie_diff').iloc[0]
            
            # Add to meal plan
            meal_plan.append({
                'subcategory': selected_food['subcategory'],
                'food': selected_food['food'],
                'serving': selected_food['serving'],
                'calories': selected_food['calories']
            })
            
            # Update tracking variables
            remaining_calories -= selected_food['calories']
            used_subcategories.add(selected_food['subcategory'])
    
    else:
        # For vegetarian and vegan plans, select from different subcategories
        # Group foods by subcategory
        subcategory_groups = {}
        for subcat in subcategories:
            subcategory_groups[subcat] = foods_df[foods_df['subcategory'] == subcat].copy()
        
        # Try to include items from at least 4 different subcategories if possible
        target_num_subcats = min(4, len(subcategory_groups))
        major_subcats = random.sample(list(subcategory_groups.keys()), target_num_subcats)
        
        # Process one subcategory at a time to ensure variety
        for i, subcat in enumerate(major_subcats):
            # For each subcategory, allocate a portion of the total calories
            if i == len(major_subcats) - 1:
                # Last category gets all remaining calories
                subcat_target_calories = remaining_calories
            else:
                # Otherwise, allocate calories evenly with some randomness
                subcat_target_calories = int(remaining_calories / (len(major_subcats) - i) * 
                                          random.uniform(0.8, 1.2))
                
            # Select an item from this subcategory
            subcat_foods = subcategory_groups[subcat]
            if not subcat_foods.empty:
                # Filter for reasonable calorie amounts relative to this subcategory's target
                reasonable_foods = subcat_foods[subcat_foods['calories'] <= subcat_target_calories]
                
                if reasonable_foods.empty:
                    # If no foods fit, get the lowest calorie options
                    reasonable_foods = subcat_foods.sort_values('calories').head(5)
                
                # Find the food with closest calories to the target
                reasonable_foods['calorie_diff'] = abs(reasonable_foods['calories'] - subcat_target_calories)
                selected_food = reasonable_foods.sort_values('calorie_diff').iloc[0]
                
                meal_plan.append({
                    'subcategory': selected_food['subcategory'],
                    'food': selected_food['food'],
                    'serving': selected_food['serving'],
                    'calories': selected_food['calories']
                })
                
                # Update remaining calories
                remaining_calories -= selected_food['calories']
                used_subcategories.add(selected_food['subcategory'])
            
            # If we've run out of calories, stop adding items
            if remaining_calories <= 0:
                break
    
    # Ensure we have exactly 4 items if possible
    if len(meal_plan) < 4:
        # We need to add more items to get to 4
        remaining_subcats = [subcat for subcat in subcategories if subcat not in used_subcategories]
        remaining_foods = foods_df[
            (~foods_df['food'].isin([item['food'] for item in meal_plan])) &
            (foods_df['calories'] <= remaining_calories)
        ]
        
        # If we have subcategories left to use, prioritize those
        if remaining_subcats and not remaining_foods.empty:
            chosen_subcats = random.sample(remaining_subcats, min(4-len(meal_plan), len(remaining_subcats)))
            additional_foods = remaining_foods[remaining_foods['subcategory'].isin(chosen_subcats)]
            
            if additional_foods.empty:
                additional_foods = remaining_foods
            
            # Add foods until we reach 4 items or run out of eligible foods
            while len(meal_plan) < 4 and not additional_foods.empty:
                # Choose the item that best fits remaining calories
                additional_foods['calorie_diff'] = abs(additional_foods['calories'] - remaining_calories/(4-len(meal_plan)))
                selected_food = additional_foods.sort_values('calorie_diff').iloc[0]
                
                meal_plan.append({
                    'subcategory': selected_food['subcategory'],
                    'food': selected_food['food'],
                    'serving': selected_food['serving'],
                    'calories': selected_food['calories']
                })
                
                # Update tracking
                remaining_calories -= selected_food['calories']
                used_subcategories.add(selected_food['subcategory'])
                
                # Remove this food from consideration
                additional_foods = additional_foods[additional_foods['food'] != selected_food['food']]
    
    # If we somehow ended up with more than 4 items, keep only the best 4
    if len(meal_plan) > 4:
        # Calculate how far the total is from target
        total_calories = sum(item['calories'] for item in meal_plan)
        excess_calories = total_calories - target_calories
        
        # If we have excess calories, remove items to get closer to target
        if excess_calories > 0:
            # Try to find an item close to the excess
            meal_plan_df = pd.DataFrame(meal_plan)
            meal_plan_df['calorie_diff'] = abs(meal_plan_df['calories'] - excess_calories)
            
            # Sort by difference and try to keep items from different subcategories
            meal_plan_df = meal_plan_df.sort_values('calorie_diff')
            
            # Start with all items
            keep_items = meal_plan.copy()
            
            # Remove items until we have 4
            while len(keep_items) > 4:
                # Find the item that, when removed, keeps us closest to target
                best_removal = None
                best_diff = float('inf')
                
                for item in keep_items:
                    # Calculate new total without this item
                    new_total = sum(i['calories'] for i in keep_items if i != item)
                    diff = abs(new_total - target_calories)
                    
                    if diff < best_diff:
                        best_diff = diff
                        best_removal = item
                
                if best_removal:
                    keep_items.remove(best_removal)
            
            meal_plan = keep_items
        else:
            # We don't have excess calories, so keep the 4 items with best subcategory variety
            used_subcats = set()
            keep_items = []
            
            # First pass - keep one from each subcategory
            for item in meal_plan:
                if item['subcategory'] not in used_subcats and len(keep_items) < 4:
                    keep_items.append(item)
                    used_subcats.add(item['subcategory'])
            
            # If we still don't have 4, add remaining items based on calories
            remaining_items = [item for item in meal_plan if item not in keep_items]
            remaining_items.sort(key=lambda x: abs(target_calories/4 - x['calories']))
            
            while len(keep_items) < 4 and remaining_items:
                keep_items.append(remaining_items.pop(0))
            
            meal_plan = keep_items
    
    return meal_plan

# We've replaced the old function with direct logic in generate_balanced_meal_plan
