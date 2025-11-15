"""
Username Analyzer - Fetch and analyze social media profiles by username.
This script allows users to enter a username and get a detailed analysis of the profile.
"""
import os
import tweepy
from dotenv import load_dotenv
from enhanced_predictor import FakeProfileDetector

class ProfileFetcher:
    def __init__(self):
        """Initialize the Twitter API client."""
        load_dotenv()  # Load environment variables from .env file
        self.api = self._get_twitter_api()
        self.detector = FakeProfileDetector()
    
    def _get_twitter_api(self):
        """Initialize and return Twitter API client."""
        try:
            # Get API credentials from environment variables
            consumer_key = os.getenv('TWITTER_API_KEY')
            consumer_secret = os.getenv('TWITTER_API_SECRET')
            access_token = os.getenv('TWITTER_ACCESS_TOKEN')
            access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            
            if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
                print("Error: Twitter API credentials not found in environment variables.")
                print("Please create a .env file with the following variables:")
                print("TWITTER_API_KEY=your_api_key")
                print("TWITTER_API_SECRET=your_api_secret")
                print("TWITTER_ACCESS_TOKEN=your_access_token")
                print("TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret")
                return None
                
            # Authenticate with Twitter API
            auth = tweepy.OAuth1UserHandler(
                consumer_key, 
                consumer_secret,
                access_token,
                access_token_secret
            )
            return tweepy.API(auth, wait_on_rate_limit=True)
            
        except Exception as e:
            print(f"Error initializing Twitter API: {e}")
            return None
    
    def fetch_profile(self, username: str) -> dict:
        """
        Fetch user profile data by username.
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            Dictionary containing profile data, or None if not found
        """
        if not self.api:
            print("API not initialized. Cannot fetch profile.")
            return None
            
        try:
            # Remove @ if present
            username = username.lstrip('@')
            
            # Fetch user data
            user = self.api.get_user(screen_name=username, include_entities=False)
            
            # Convert to dictionary and extract relevant fields
            user_data = user._json
            
            # Format the data for our detector
            profile = {
                'id_str': user_data.get('id_str', ''),
                'name': user_data.get('name', ''),
                'screen_name': user_data.get('screen_name', ''),
                'description': user_data.get('description', ''),
                'statuses_count': user_data.get('statuses_count', 0),
                'followers_count': user_data.get('followers_count', 0),
                'friends_count': user_data.get('friends_count', 0),
                'favourites_count': user_data.get('favourites_count', 0),
                'listed_count': user_data.get('listed_count', 0),
                'verified': int(user_data.get('verified', False)),
                'default_profile': int(user_data.get('default_profile', True)),
                'default_profile_image': int(user_data.get('default_profile_image', True)),
                'geo_enabled': int(user_data.get('geo_enabled', False)),
                'created_at': user_data.get('created_at', ''),
                'location': user_data.get('location', ''),
                'url': user_data.get('url', ''),
                'profile_image_url': user_data.get('profile_image_url', ''),
                'profile_banner_url': user_data.get('profile_banner_url', '')
            }
            
            return profile
            
        except tweepy.TweepError as e:
            if e.api_code == 50:
                print(f"User @{username} not found.")
            elif e.api_code == 63:
                print(f"User @{username} has been suspended.")
            else:
                print(f"Error fetching profile: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    
    def analyze_username(self, username: str):
        """
        Fetch and analyze a profile by username.
        
        Args:
            username: Twitter username (with or without @)
        """
        print(f"\nFetching data for @{username.lstrip('@')}...")
        
        # Fetch profile data
        profile = self.fetch_profile(username)
        if not profile:
            print(f"Could not fetch data for @{username}")
            return
        
        # Display basic profile info
        self._display_profile_info(profile)
        
        # Analyze the profile
        result = self.detector.predict(profile)
        
        # Display analysis results
        self._display_analysis_results(result)
    
    def _display_profile_info(self, profile: dict):
        """Display basic profile information."""
        print("\n" + "="*50)
        print(f"👤 @{profile['screen_name']} - {profile['name']}")
        if profile.get('verified'):
            print("✅ Verified Account")
        print("-" * 50)
        
        if profile.get('description'):
            print(f"\n📝 Bio: {profile['description']}")
        
        if profile.get('location'):
            print(f"📍 Location: {profile['location']}")
        
        if profile.get('url'):
            print(f"🔗 Website: {profile['url']}")
        
        print("\n📊 Stats:")
        print(f"  • Tweets: {profile['statuses_count']:,}")
        print(f"  • Following: {profile['friends_count']:,}")
        print(f"  • Followers: {profile['followers_count']:,}")
        print(f"  • Likes: {profile['favourites_count']:,}")
        print(f"  • Listed: {profile['listed_count']:,}")
        
        if profile.get('created_at'):
            print(f"  • Joined: {profile['created_at']}")
        
        if profile['default_profile_image']:
            print("\n⚠️  Default profile image detected")
        
        print("="*50 + "\n")
    
    def _display_analysis_results(self, result: dict):
        """Display the analysis results."""
        if 'error' in result:
            print(f"Error during analysis: {result['error']}")
            return
        
        print("🔍 Profile Analysis Results:")
        print("-" * 50)
        
        # Display prediction
        if result['is_fake']:
            print("❌ Prediction: POTENTIALLY FAKE PROFILE")
        else:
            print("✅ Prediction: LIKELY GENUINE PROFILE")
        
        # Display confidence level
        confidence = result['confidence'] * 100
        if confidence > 80:
            confidence_str = f"High ({confidence:.1f}%)"
        elif confidence > 60:
            confidence_str = f"Medium ({confidence:.1f}%)"
        else:
            confidence_str = f"Low ({confidence:.1f}%)"
        
        print(f"\n🔄 Confidence: {confidence_str}")
        
        # Display probabilities
        print("\n📊 Probability Breakdown:")
        print(f"  • Genuine: {result['probability_genuine']*100:.1f}%")
        print(f"  • Fake: {result['probability_fake']*100:.1f}%")
        
        # Display top contributing features
        if result.get('top_features'):
            print("\n🔍 Key Factors:")
            for feat in result['top_features'][:3]:  # Show top 3 features
                feature_name = feat['feature'].replace('_', ' ').title()
                importance = feat['importance'] * 100
                print(f"  • {feature_name}: {importance:.1f}%")
        
        # Display warnings for suspicious indicators
        if result['is_fake']:
            print("\n🚨 Warning Signs:")
            features = result.get('all_features', {})
            
            if features.get('default_profile_image'):
                print("  • Default profile image")
                
            if features.get('bio_spam_score', 0) > 0.5:
                print("  • Bio contains potential spam terms")
                
            if features.get('username_has_repeating_chars'):
                print("  • Suspicious username pattern")
                
            if features.get('followers_count', 0) == 0:
                print("  • No followers")
                
            if features.get('followers_count', 0) > 0 and features.get('friends_count', 0) > 0:
                ratio = features['followers_count'] / features['friends_count']
                if ratio < 0.1:  # Very low follower/following ratio
                    print(f"  • Low follower/following ratio (1:{int(1/ratio)})")
        
        print("\n💡 Note: This is an automated analysis. Always use your own judgment.")
        print("="*50 + "\n")

def main():
    """Main interactive function."""
    print("\n" + "="*60)
    print("🔍 Username Analyzer - Fake Profile Detection")
    print("Enter a username to analyze (or 'q' to quit)")
    print("Example: elonmusk or @elonmusk")
    print("="*60)
    
    analyzer = ProfileFetcher()
    
    while True:
        username = input("\nEnter username: ").strip()
        
        if username.lower() in ['q', 'quit', 'exit']:
            print("Goodbye! 👋")
            break
            
        if not username:
            print("Please enter a username.")
            continue
            
        analyzer.analyze_username(username)

if __name__ == "__main__":
    main()
