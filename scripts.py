#this will be where we hold some scripts just for better organization


## Part 1: Importing Data
import pandas as pd
import os
import json
import matplotlib.pyplot as plt

def load_and_prepare_data():
    """Load and prepare the USDA food dataset."""
    food = pd.read_csv("Data/foundationfoodcsv/food.csv")
    food_nutrient = pd.read_csv("Data/foundationfoodcsv/food_nutrient.csv")
    nutrient = pd.read_csv("Data/foundationfoodcsv/nutrient.csv")
    food_category = pd.read_csv("Data/foundationfoodcsv/food_category.csv")

    food_nutrient = food_nutrient.merge(
        nutrient, 
        left_on="nutrient_id", 
        right_on="id", 
        how="left"
    )

    combined = food.merge(
        food_nutrient, 
        on="fdc_id", 
        how="left"
    )


    combined = combined.merge(
        food_category, 
        left_on="food_category_id", 
        right_on="id", 
        how="left"
    )


    relevant_nutrients = ["Energy", "Protein", "Carbohydrate, by difference", "Total lipid (fat)"]
    nutrient_focus = combined[combined["name"].isin(relevant_nutrients)]


    foundationfood = nutrient_focus.pivot_table(
        index=["fdc_id", "description_x", "description_y"],
        columns="name",
        values="amount",
        aggfunc="first"
    ).reset_index()


    foundationfood.rename(columns={
        "description_x": "food_description",
        "description_y": "food_category",
        "Energy": "Calories",
        "Protein": "Protein (g)",
        "Carbohydrate, by difference": "Carbohydrates (g)",
        "Total lipid (fat)": "Fat (g)"
    }, inplace=True)

    return foundationfood



##Part 2: Options for saving and retrieving plates
data_folder = "Data"
user_data_file = os.path.join(data_folder, "user_plates.json")

if not os.path.exists(data_folder):
    os.makedirs(data_folder)

if not os.path.exists(user_data_file):
    with open(user_data_file, 'w') as file:
        json.dump({}, file)

def save_plate(username, password, plate, file_path):
    """Save the user's plate to a JSON file."""
    with open(file_path, 'r') as file:
        user_data = json.load(file)
    user_data[username] = {"password": password, "plate": plate}
    with open(file_path, 'w') as file:
        json.dump(user_data, file, indent=4)
    print(f"Plate saved for user '{username}'!")

def retrieve_plate(username, password, file_path):
    """Retrieve the user's plate if user and pass work"""
    with open(file_path, 'r') as file:
        user_data = json.load(file)
    if username in user_data:
        if user_data[username]["password"] == password:
            return user_data[username]["plate"]
        else:
            return "Incorrect password."
    else:
        return "Username not found."


##Part 3 and 4 Data Visualization
def get_nutritional_data(plate, usda_data):
    """
    Fetch nutritional data for the selected foods from the USDA dataset
    Parameters:
        plate (list): List of food items selected by the user
        usda_data (DataFrame): USDA dataset with nutritional information.
    Returns:
        dict: Nutritional data for the selected foods.
    """
    nutritional_data = {}
    for item in plate:
        food_info = usda_data[
            (usda_data["food_description"].str.contains(item, case=False)) &
            (usda_data["Calories"] < 1000)
        ]        
        
        if not food_info.empty:
            valid_foods = food_info.dropna(subset=["Calories", "Protein (g)", "Carbohydrates (g)", "Fat (g)"])
            
            if not valid_foods.empty:
                match = valid_foods.loc[valid_foods["Calories"].idxmin()]  # we ran into the problem of foods with extreme calories being first 
                nutritional_data[item] = {
                    "calories": match["Calories"],
                    "protein": match["Protein (g)"],
                    "carbs": match["Carbohydrates (g)"],
                    "fats": match["Fat (g)"],
                    "group": match["food_category"]
                }
            else:
                print(f"Not enough nutrient info on '{item}' – skipping .")
        else:
            print(f"Food '{item}' not found in USDA data.")
    return nutritional_data

def visualize_plate(plate, nutritional_data):
    """
    Generate visualizations for the Healthy Plate Builder.

    Parameters:
        plate (list): List of foods selected by the user.
        nutritional_data (dict): Dictionary containing nutritional information for each food.
    """
    # recommended daily values based on FDA
    recommended_values = {
        "Calories": 2000,
        "Protein (g)": 50,
        "Carbohydrates (g)": 275,
        "Fat (g)": 78
    }

    # getting nutritional values
    total_nutrients = {
        "Calories": 0,
        "Protein (g)": 0,
        "Carbohydrates (g)": 0,
        "Fat (g)": 0
    }
    food_groups = {}

    for item in plate:          
        if item in nutritional_data:
            data = nutritional_data[item]
            total_nutrients["Calories"] += data["calories"]
            total_nutrients["Protein (g)"] += data["protein"]
            total_nutrients["Carbohydrates (g)"] += data["carbs"]
            total_nutrients["Fat (g)"] += data["fats"]
            food_groups[data["group"]] = food_groups.get(data["group"], 0) + 1

    # calculating percentage of daily recommended values
    percentages = [
        min((total_nutrients["Calories"] / recommended_values["Calories"]) * 100, 100),
        min((total_nutrients["Protein (g)"] / recommended_values["Protein (g)"]) * 100, 100),
        min((total_nutrients["Carbohydrates (g)"] / recommended_values["Carbohydrates (g)"]) * 100, 100),
        min((total_nutrients["Fat (g)"] / recommended_values["Fat (g)"]) * 100, 100)
    ]

    # Visualization 1: Pie Chart for Food Group Distribution
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    if food_groups:
        plt.pie(food_groups.values(), labels=food_groups.keys(), autopct='%1.1f%%', startangle=140)
        plt.title("Food Group Distribution")
    else:
        plt.text(0.5, 0.5, "No Food Groups Selected", ha='center', va='center', fontsize=12)
        plt.title("Food Group Distribution")

    # Visualization 2: Bar Graph for Nutrient Breakdown vs. Recommended Values
    plt.subplot(1, 2, 2)
    nutrient_labels = ["Calories", "Protein (g)", "Carbohydrates (g)", "Fat (g)"]
    bars = plt.bar(nutrient_labels, percentages, color=["pink", "green", "teal", "yellow"])
    plt.title("Nutritional Intake vs. Daily Recommended Values")
    plt.ylabel("Percentage of Recommended Value (%)")
    plt.ylim(0, 100)

    # show visualizations
    for bar, percentage in zip(bars, percentages):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height + 1, f"{height:.1f}%", ha='center')

    plt.show()


