"""
Enhanced Fake Profile Detection System
This module provides advanced fake profile detection using machine learning.
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from enhanced_features import ProfileAnalyzer

class FakeProfileDetector:
    def __init__(self, model_path: str = 'saved_model/random_forest_model.pkl'):
        """
        Initialize the fake profile detector.
        
        Args:
            model_path: Path to the trained model file
        """
        self.analyzer = ProfileAnalyzer()
        self.model = None
        self.feature_columns = None
        self.model_path = model_path
        self.load_model()
    
    def load_model(self):
        """Load the trained model and feature columns."""
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.feature_columns = model_data['feature_columns']
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def preprocess_features(self, features: Dict[str, Any]) -> pd.DataFrame:
        """
        Preprocess and align features with model expectations.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            pd.DataFrame: Processed features in the correct format
        """
        # Create a DataFrame with all possible columns filled with zeros
        processed = pd.DataFrame(columns=self.feature_columns)
        
        # Fill in the available features
        for col in processed.columns:
            if col in features:
                processed[col] = [features[col]]
            else:
                # Fill missing columns with appropriate defaults
                if col in ['default_profile', 'default_profile_image', 'geo_enabled', 'verified',
                         'username_has_numbers', 'username_has_special_chars', 
                         'username_has_repeating_chars', 'bio_has_url', 'bio_has_emoji',
                         'gender_male', 'gender_female']:
                    processed[col] = [0]  # Binary features default to 0
                else:
                    processed[col] = [0.0]  # Numerical features default to 0.0
        
        return processed
    
    def predict(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if a profile is fake.
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Dict with prediction results
        """
        if not self.model or not self.feature_columns:
            raise ValueError("Model not loaded properly")
        
        try:
            # Extract features
            features = self.analyzer.extract_features(profile_data)
            
            # Preprocess features to match model input format
            processed_features = self.preprocess_features(features)
            
            # Make prediction
            prediction = self.model.predict(processed_features)[0]
            proba = self.model.predict_proba(processed_features)[0]
            
            # Get feature importance
            if hasattr(self.model, 'feature_importances_'):
                importances = dict(zip(processed_features.columns, 
                                    self.model.feature_importances_))
                top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:3]
            else:
                top_features = []
            
            return {
                'is_fake': bool(prediction == 0),  # Assuming 0 is fake, 1 is genuine
                'confidence': float(max(proba)),
                'probability_fake': float(proba[0]),
                'probability_genuine': float(proba[1]),
                'top_features': [{'feature': f[0], 'importance': float(f[1])} 
                               for f in top_features],
                'all_features': features
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'is_fake': None,
                'confidence': 0.0
            }

def check_profile_interactive():
    """Interactive function to check a profile."""
    print("\n=== Enhanced Fake Profile Detector ===")
    print("Please enter the following profile details (press Enter to skip):")
    
    # Get user input
    profile = {
        'name': input("Full name: "),
        'screen_name': input("Username: "),
        'description': input("Bio/Description: "),
        'statuses_count': int(input("Number of posts/statuses: ") or "0"),
        'followers_count': int(input("Number of followers: ") or "0"),
        'friends_count': int(input("Number of people following: ") or "0"),
        'favourites_count': int(input("Number of favorites/likes: ") or "0"),
        'listed_count': int(input("Number of lists: ") or "0"),
        'verified': int(input("Verified account? (1 for yes, 0 for no): ") or "0"),
        'default_profile': int(input("Using default profile? (1 for yes, 0 for no): ") or "1"),
        'default_profile_image': int(input("Using default profile image? (1 for yes, 0 for no): ") or "1"),
        'geo_enabled': int(input("Has location enabled? (1 for yes, 0 for no): ") or "0"),
        'created_at': input("Account creation date (e.g., 'Fri May 18 10:28:11 +0000 2007'): ") or None
    }
    
    # Make prediction
    detector = FakeProfileDetector()
    result = detector.predict(profile)
    
    # Display results
    print("\n=== Profile Analysis ===")
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"Prediction: {'FAKE' if result['is_fake'] else 'GENUINE'}")
    print(f"Confidence: {result['confidence']*100:.1f}%")
    print(f"Probability Fake: {result['probability_fake']*100:.1f}%")
    print(f"Probability Genuine: {result['probability_genuine']*100:.1f}%")
    
    if result['top_features']:
        print("\nTop contributing features:")
        for feat in result['top_features']:
            print(f"- {feat['feature']}: {feat['importance']*100:.1f}%")
    
    if result['is_fake']:
        print("\n🚨 Warning: This profile shows signs of being fake. Be cautious!")
        
        # Provide reasoning based on features
        reasons = []
        features = result['all_features']
        
        if features.get('default_profile_image', 0) == 1:
            reasons.append("Default profile image")
            
        if features.get('bio_spam_score', 0) > 0.5:
            reasons.append("Bio contains spam-like content")
            
        if features.get('username_has_repeating_chars', 0) == 1:
            reasons.append("Suspicious username pattern")
            
        if features.get('followers_count', 0) == 0:
            reasons.append("No followers")
            
        if reasons:
            print("\nPotential reasons for flagging:", ", ".join(reasons))
    else:
        print("\n✅ This profile appears to be genuine.")

if __name__ == "__main__":
    check_profile_interactive()
