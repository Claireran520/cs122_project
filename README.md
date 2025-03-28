# CS 122 Project

## Project Title:
Calorie Buddy

## Authors:
Xiaoke Ran, Sania Bandekar

## Project Description:
The desktop application enables users to input their desired daily calorie intake, and it generates four optimized meal combinations that align with the specified calorie target. The generated meal options include:
- Vegetarian – A selection of plant-based meals.
- Non-Vegetarian – A combination of meals containing meat or poultry.
- Seafood Mix – A variety of meals incorporating seafood.
- Vegan – Completely plant-based meals, free from animal products.
Each meal combination is carefully calculated to ensure that the total calorie content does not exceed the user's specified intake. The application provides these four options as potential meal plans for users to choose from, offering flexibility based on dietary preferences.
## Project Outline
1. Interface Plan
The desktop application will feature a user-friendly graphical interface that allows users to input their desired daily calorie intake. The key interface components will include:
Input Section: A field for users to enter their calorie target.
Generate Button: A button that triggers the calculation and displays meal combinations. A button that refreshes and displays meal combinations if users are not satisfied with the first generation and it can be repeated.
Output Display: A visually organized section that presents four meal combination options:
Vegetarian, Non-Vegetarian, Seafood Mix, Vegan
Additional Features(May Include): saving meal preferences, Records of the selected combination for the past week, Calories intake calculation for the week.

2. Data Collection and Storage Plan (Written by Xiaoke Ran)
This section will outline the methods for sourcing, storing, and managing food-related data, ensuring accuracy and efficiency in calorie-based meal generation. Key components include:
Data Sources:
Public food nutrition website: https://www.calories.info
Additional: User-inputted food items 
Storage Strategy:
Scrape source website to obtain and store food items, calorie values into a .csv file.Indexed data for efficient retrieval and combination generation
Data Integrity & Updates:
Regular updates to keep nutritional information accurate
Data validation techniques to prevent errors in meal calculations






## A .gitignore file and a license
.DS_Store 
BSD 3-Clause License


