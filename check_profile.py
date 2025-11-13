import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load the trained model and preprocessing objects
model_data = joblib.load('saved_model/random_forest_model.pkl')
model = model_data['model']
lang_dict = model_data['lang_dict']

def predict_gender(name):
    """Simple gender prediction from name"""
    if not name or not isinstance(name, str):
        return 0
    first_name = name.split(' ')[0].lower()
    # Simple heuristic based on name endings
    female_endings = ['a', 'e', 'i', 'y']
    male_endings = ['o', 'r', 's', 't', 'n']
    
    if any(first_name.endswith(ending) for ending in female_endings):
        return -1  # female
    elif any(first_name.endswith(ending) for ending in male_endings):
        return 1   # male
    return 0       # unknown

def check_profile():
    print("\n=== Fake Profile Detector ===")
    print("Please enter the following profile details (press Enter to skip any field):\n")
    
    # Get user input with default values
    name = input("Full name: ")
    
    try:
        statuses = int(input("Number of posts/statuses (e.g., 100): ") or "0")
        followers = int(input("Number of followers (e.g., 500): ") or "0")
        following = int(input("Number of people following (e.g., 200): ") or "0")
        favorites = int(input("Number of favorites/likes (e.g., 50): ") or "0")
        listed = int(input("Number of lists (e.g., 5): ") or "0")
        lang = (input("Language code (e.g., en, es, fr): ") or "en").lower()
    except ValueError:
        print("\nError: Please enter valid numbers for the counts.")
        return
    
    # Prepare features
    sex_code = predict_gender(name)
    lang_code = lang_dict.get(lang, 0)  # default to 0 if language not found
    
    # Create feature vector in the same order as training
    features = pd.DataFrame([[
        statuses, followers, following, favorites, listed, sex_code, lang_code
    ]], columns=model_data['feature_columns'])
    
    # Make prediction
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0]
    
    # Display results
    print("\n=== Profile Analysis ===")
    print(f"Name: {name}")
    print(f"Statuses: {statuses}, Followers: {followers}, Following: {following}")
    print(f"Favorites: {favorites}, Listed: {listed}, Language: {lang}")
    
    result = "FAKE" if prediction == 0 else "GENUINE"
    confidence = max(probability) * 100
    
    print(f"\nPrediction: {result}")
    print(f"Confidence: {confidence:.1f}%")
    
    if result == "FAKE":
        print("\n⚠️  Warning: This profile shows signs of being fake. Be cautious!")
        print("Common signs of fake profiles:")
        print("- Unusually high followers with few posts")
        print("- Very few followers compared to following")
        print("- Inconsistent activity patterns")
    else:
        print("\n✅ This profile appears to be genuine.")
        print("Common signs of genuine profiles:")
        print("- Balanced follower/following ratio")
        print("- Consistent posting activity")
        print("- Normal engagement metrics")

if __name__ == "__main__":
    try:
        while True:
            check_profile()
            if input("\nCheck another profile? (y/n): ").lower() != 'y':
                print("\nThank you for using Fake Profile Detector!")
                break
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Goodbye!")
