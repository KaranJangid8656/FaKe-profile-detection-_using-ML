import pandas as pd
import numpy as np
import joblib
import gender_guesser.detector as gender
import os

def load_model():
    """Load the trained model and preprocessing objects"""
    model_data = joblib.load('saved_model/random_forest_model.pkl')
    return model_data['model'], model_data['feature_columns'], model_data['lang_dict']

def predict_sex(name, sex_predictor):
    """Predict gender from name"""
    if not isinstance(name, str) or ' ' not in name:
        return 0  # unknown
    first_name = name.split(' ')[0]
    result = sex_predictor.get_gender(first_name)
    if result in ['female', 'mostly_female']:
        return -1  # female
    elif result in ['male', 'mostly_male']:
        return 1   # male
    else:
        return 0   # unknown

def check_profile():
    print("\n=== Fake Profile Detector ===")
    print("Please enter the following profile details:")
    
    # Get user input
    name = input("Full name: ")
    statuses = int(input("Number of posts/statuses: "))
    followers = int(input("Number of followers: "))
    following = int(input("Number of people following: "))
    favorites = int(input("Number of favorites/likes: "))
    listed = int(input("Number of lists: "))
    lang = input("Language (e.g., en, es, fr): ").lower()
    
    # Load model and preprocessing data
    model, feature_columns, lang_dict = load_model()
    
    # Map language to code
    lang_code = lang_dict.get(lang, 0)  # default to 0 if language not found
    
    # Predict gender
    sex_predictor = gender.Detector()
    sex_code = predict_sex(name, sex_pather_predictor)
    
    # Create feature vector
    features = pd.DataFrame([[
        statuses, followers, following, favorites, listed, sex_code, lang_code
    ]], columns=feature_columns)
    
    # Make prediction
    prediction = model.predict(features)
    probability = model.predict_proba(features)
    
    # Display result
    result = "FAKE" if prediction[0] == 0 else "GENUINE"
    confidence = max(probability[0]) * 100
    
    print("\n=== Profile Analysis ===")
    print(f"Prediction: {result}")
    print(f"Confidence: {confidence:.1f}%")
    
    if result == "FAKE":
        print("\nWarning: This profile shows signs of being fake. Be cautious!")
    else:
        print("\nThis profile appears to be genuine.")

if __name__ == "__main__":
    # First, make sure the model is trained and saved
    if not os.path.exists('saved_model/random_forest_model.pkl'):
        print("Model not found. Please run 'Random Forest.py' first to train the model.")
    else:
        while True:
            check_profile()
            if input("\nCheck another profile? (y/n): ").lower() != 'y':
                print("Goodbye!")
                break
