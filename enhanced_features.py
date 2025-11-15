"""
Enhanced feature extraction for fake profile detection.
This module provides functions to extract advanced features from social media profiles.
"""
import re
import numpy as np
from datetime import datetime
import gender_guesser.detector as gender
from urllib.parse import urlparse

class ProfileAnalyzer:
    def __init__(self):
        self.gender_detector = gender.Detector()
        self.common_spam_terms = {'free', 'win', 'prize', 'discount', 'offer', 'limited', 'click', 'http', 'www'}
        self.suspicious_patterns = [
            r'\d{4,}',  # 4 or more consecutive digits
            r'[^a-zA-Z0-9]',  # Non-alphanumeric characters
            r'([a-zA-Z])\1{2,}',  # 3 or more repeating characters
        ]

    def get_account_age_days(self, created_at):
        """Calculate account age in days."""
        if not created_at:
            return 0
        try:
            # Format: 'Fri May 18 10:28:11 +0000 2007'
            acc_date = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
            return (datetime.now(acc_date.tzinfo) - acc_date).days
        except (ValueError, TypeError):
            return 0

    def analyze_username(self, username):
        """Analyze username for suspicious patterns."""
        if not username:
            return {
                'username_has_numbers': 0,
                'username_has_special_chars': 0,
                'username_has_repeating_chars': 0,
                'username_length': 0
            }
            
        return {
            'username_has_numbers': int(any(char.isdigit() for char in username)),
            'username_has_special_chars': int(bool(re.search(r'[^a-zA-Z0-9_]', username))),
            'username_has_repeating_chars': int(any(re.search(pattern, username) for pattern in self.suspicious_patterns)),
            'username_length': len(username)
        }

    def analyze_bio(self, bio):
        """Analyze profile bio for spam-like content."""
        if not bio:
            return {
                'bio_has_url': 0,
                'bio_length': 0,
                'bio_spam_score': 0,
                'bio_has_emoji': 0
            }
            
        bio_lower = bio.lower()
        urls = re.findall(r'https?://\S+|www\.\S+', bio_lower)
        emojis = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', bio)
        spam_terms_count = sum(1 for term in self.common_spam_terms if term in bio_lower)
        
        return {
            'bio_has_url': int(len(urls) > 0),
            'bio_length': len(bio) if bio else 0,
            'bio_spam_score': min(spam_terms_count / 3, 1),  # Normalize to 0-1 range
            'bio_has_emoji': int(len(emojis) > 0)
        }

    def analyze_activity(self, statuses_count, followers_count, friends_count, created_at):
        """Analyze user activity patterns."""
        account_age_days = max(1, self.get_account_age_days(created_at))
        
        # Calculate rates per day
        statuses_per_day = statuses_count / account_age_days if account_age_days > 0 else 0
        followers_per_day = followers_count / account_age_days if account_age_days > 0 else 0
        friends_per_day = friends_count / account_age_days if account_age_days > 0 else 0
        
        # Engagement ratio (avoid division by zero)
        engagement_ratio = (followers_count / friends_count) if friends_count > 0 else (followers_count + 1)
        
        return {
            'statuses_per_day': statuses_per_day,
            'followers_per_day': followers_per_day,
            'friends_per_day': friends_per_day,
            'engagement_ratio': engagement_ratio,
            'followers_to_following_ratio': engagement_ratio,
            'account_age_days': account_age_days
        }

    def extract_features(self, profile_data):
        """Extract all features from profile data."""
        # Basic features
        features = {
            'statuses_count': int(profile_data.get('statuses_count', 0)),
            'followers_count': int(profile_data.get('followers_count', 0)),
            'friends_count': int(profile_data.get('friends_count', 0)),
            'favourites_count': int(profile_data.get('favourites_count', 0)),
            'listed_count': int(profile_data.get('listed_count', 0)),
            'default_profile': int(profile_data.get('default_profile', 1)),
            'default_profile_image': int(profile_data.get('default_profile_image', 1)),
            'geo_enabled': int(profile_data.get('geo_enabled', 0)),
            'verified': int(profile_data.get('verified', 0)),
        }
        
        # Add username analysis
        username = profile_data.get('screen_name', '')
        features.update(self.analyze_username(username))
        
        # Add bio analysis
        bio = profile_data.get('description', '')
        features.update(self.analyze_bio(bio))
        
        # Add activity analysis
        activity_features = self.analyze_activity(
            features['statuses_count'],
            features['followers_count'],
            features['friends_count'],
            profile_data.get('created_at')
        )
        features.update(activity_features)
        
        # Add gender prediction
        name = profile_data.get('name', '')
        if name and isinstance(name, str) and ' ' in name:
            first_name = name.split(' ')[0]
            gender_pred = self.gender_detector.get_gender(first_name)
            features['gender_male'] = 1 if gender_pred in ['male', 'mostly_male'] else 0
            features['gender_female'] = 1 if gender_pred in ['female', 'mostly_female'] else 0
        else:
            features['gender_male'] = 0
            features['gender_female'] = 0
            
        return features
