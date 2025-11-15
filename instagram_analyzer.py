"""
Instagram Profile Analyzer - Detect fake Instagram profiles
This script analyzes Instagram profiles to determine their authenticity.
"""
import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
import instaloader
from tqdm import tqdm
from dotenv import load_dotenv
class FakeProfileDetector:
    """Basic fake profile detector for Instagram."""
    
    def predict(self, profile_data):
        """Make a basic prediction based on profile data."""
        # Simple heuristics for fake profile detection
        risk_score = 0
        reasons = []
        
        # Check for suspicious follower/following ratio
        followers = profile_data.get('followers', 0)
        following = profile_data.get('followees', 0)
        
        if followers > 0:
            ratio = following / followers
            if ratio > 10:  # Following way more than followers
                risk_score += 30
                reasons.append(f"High following/followers ratio ({ratio:.1f})")
        
        # Check for new accounts
        account_age_days = profile_data.get('account_age_days', 0)
        if account_age_days > 0 and account_age_days < 30:  # Less than 30 days old
            risk_score += 20
            reasons.append(f"New account ({account_age_days} days old)")
        
        # Check for lack of posts
        if profile_data.get('posts', 0) == 0:
            risk_score += 15
            reasons.append("No posts")
        
        # Check for default or no profile picture
        if not profile_data.get('has_profile_pic', False):
            risk_score += 10
            reasons.append("No profile picture")
        
        # Determine if profile is likely fake
        is_fake = risk_score > 30
        confidence = min(100, risk_score * 1.5)  # Scale to 0-100%
        
        return {
            'is_fake': is_fake,
            'confidence': confidence,
            'risk_score': risk_score,
            'reasons': reasons,
            'top_features': [(r, 0) for r in reasons]  # For compatibility
        }

class InstagramAnalyzer:
    def __init__(self):
        """Initialize the Instagram analyzer."""
        self.L = instaloader.Instaloader()
        self.detector = FakeProfileDetector()
        self.session_file = 'instagram_session'
        self._login()
    
    def _login(self):
        """Attempt to login to Instagram with saved session or credentials."""
        try:
            # Try to load existing session first
            try:
                if os.path.exists(self.session_file):
                    self.L.load_session_from_file('instagram_session')
                    # Test if session is still valid
                    test_profile = instaloader.Profile.from_username(self.L.context, 'instagram')
                    print("✅ Using existing Instagram session")
                    return True
            except Exception as e:
                print(f"⚠️  Session expired or invalid: {str(e)}")
                if os.path.exists(self.session_file):
                    os.remove(self.session_file)
            
            # If no valid session, try to login with credentials
            load_dotenv()
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            
            if not username or not password:
                print("⚠️  Instagram credentials not found in .env file")
                return False
            
            try:
                print("🔑 Attempting to login to Instagram...")
                self.L.login(username, password)
                self.L.save_session_to_file(self.session_file)
                print("✅ Successfully logged in to Instagram")
                return True
            except Exception as e:
                print(f"❌ Login failed: {str(e)}")
                if "checkpoint_required" in str(e).lower():
                    print("🔒 Instagram is asking for verification. Please check your email or phone.")
                return False
            
        except Exception as e:
            print(f"⚠️  Could not login to Instagram: {str(e)}")
            print("Continuing with limited functionality (public profiles only)")
            return False
    
    def get_profile(self, username: str) -> Optional[Dict]:
        """Fetch and process Instagram profile data."""
        username = username.lower().lstrip('@')
        print(f"\n🔍 Fetching @{username}'s profile...")
        
        # Clear any existing session data
        if hasattr(self, 'L'):
            self.L.close()
            self.L = instaloader.Instaloader()
            self._login()  # Re-authenticate
        
        try:
            # Get profile data with error handling and retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    profile = instaloader.Profile.from_username(self.L.context, username)
                    break  # If successful, exit the retry loop
                except instaloader.exceptions.ProfileNotExistsException:
                    print(f"❌ Profile @{username} does not exist")
                    return None
                except instaloader.exceptions.PrivateProfileNotFollowedException:
                    print(f"🔒 Profile @{username} is private. Login with your credentials to view.")
                    return None
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"❌ Error accessing profile after {max_retries} attempts: {str(e)}")
                        return None
                    print(f"⚠️  Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)  # Wait before retry
            
            # Get recent posts for additional analysis
            posts = []
            max_posts = 12  # Get more posts for better analysis
            
            if profile.mediacount > 0:
                print(f"📥 Fetching up to {min(max_posts, profile.mediacount)} recent posts...")
                try:
                    post_iterator = profile.get_posts()
                    for post in post_iterator:
                        try:
                            # Get post details with error handling
                            post_data = {
                                'likes': getattr(post, 'likes', 0),
                                'comments': getattr(post, 'comments', 0),
                                'is_video': getattr(post, 'is_video', False),
                                'caption': getattr(post, 'caption_text', ''),
                                'hashtags': getattr(post, 'caption_hashtags', []),
                                'mentions': getattr(post, 'caption_mentions', []),
                                'timestamp': getattr(post, 'date_utc', None)
                            }
                            posts.append(post_data)
                            
                            if len(posts) >= max_posts:
                                break
                                
                        except Exception as post_error:
                            print(f"⚠️  Error processing post: {str(post_error)[:100]}...")
                            continue
                            
                    print(f"✅ Analyzed {len(posts)} recent posts")
                    
                except Exception as e:
                    print(f"⚠️  Could not fetch posts: {str(e)}")
                    if '429' in str(e):
                        print("⚠️  Instagram rate limit reached. Please try again later.")
            else:
                print("ℹ️  This profile has no posts")
            
            # Calculate engagement metrics with safe attribute access
            total_likes = 0
            total_comments = 0
            
            for p in posts:
                try:
                    total_likes += p.get('likes', 0) or 0
                    total_comments += p.get('comments', 0) or 0
                except (AttributeError, TypeError):
                    continue
                    
            avg_likes = total_likes / len(posts) if posts else 0
            avg_comments = total_comments / len(posts) if posts else 0
            
            # Calculate engagement rate (likes + comments) / followers * 100
            engagement_rate = 0
            if profile.followers > 0 and posts:
                total_engagement = total_likes + total_comments
                engagement_rate = (total_engagement / (profile.followers * len(posts))) * 100
            
            # Prepare profile data with direct attribute access and better error handling
            try:
                # Get basic profile info with error handling
                username = getattr(profile, 'username', 'unknown')
                full_name = getattr(profile, 'full_name', '')
                biography = getattr(profile, 'biography', '')
                external_url = getattr(profile, 'external_url', '')
                
                # Get counts with fallback
                followers = getattr(profile, 'followers', 0)
                following = getattr(profile, 'followees', 0)
                total_posts = getattr(profile, 'mediacount', 0)
                is_private = int(getattr(profile, 'is_private', False))
                is_verified = int(getattr(profile, 'is_verified', False))
                
                # Debug output
                print("\n📊 Raw Profile Data:")
                print(f"Username: {username}")
                print(f"Name: {full_name}")
                print(f"Bio: {biography[:100]}..." if biography else "No bio")
                print(f"Followers: {followers:,}")
                print(f"Following: {following:,}")
                print(f"Total Posts: {total_posts:,}")
                print(f"Private: {'Yes' if is_private else 'No'}")
                print(f"Verified: {'Yes' if is_verified else 'No'}")
                
                # Calculate account age if possible
                account_age_days = 0
                try:
                    if hasattr(profile, 'created_date'):
                        account_age = datetime.now(profile.created_date.tzinfo) - profile.created_date
                        account_age_days = account_age.days
                except:
                    pass
                
                # Prepare profile data
                profile_data = {
                    'username': username,
                    'full_name': full_name,
                    'biography': biography,
                    'external_url': external_url,
                    'followers': followers,
                    'followees': following,
                    'posts': total_posts,
                    'is_private': is_private,
                    'is_verified': is_verified,
                    'has_profile_pic': 1 if profile.profile_pic_url else 0,
                    'has_default_profile_pic': 0,  # Hard to determine without more info
                    'has_highlight_reels': 0,  # Not available in current API
                    'has_igtv': int(hasattr(profile, 'igtvcount') and profile.igtvcount > 0),
                    'has_guides': 0,  # Not available
                    'has_clips': 0,   # Not available
                    'avg_likes': avg_likes,
                    'avg_comments': avg_comments,
                    'engagement_rate': engagement_rate,
                    'is_business_account': int(hasattr(profile, 'is_business_account') and profile.is_business_account),
                    'business_category': getattr(profile, 'business_category_name', ''),
                    'created_at': getattr(profile, 'created_date', ''),
                    'account_age_days': account_age_days,
                    'recent_posts_count': len(posts),
                    'recent_hashtags': list(set(h for p in posts for h in p.get('hashtags', []))),
                    'recent_mentions': list(set(m for p in posts for m in p.get('mentions', []))),
                }
                
                # Debug output
                print("\n📊 Fetched Profile Data:")
                print(f"👤 {full_name} (@{username})")
                print(f"📌 Followers: {followers:,} | Following: {following:,} | Posts: {total_posts:,}")
                if biography:
                    print(f"📝 Bio: {biography[:100]}{'...' if len(biography) > 100 else ''}")
                
            except Exception as e:
                print(f"⚠️  Error processing profile data: {str(e)}")
                raise
            
            return profile_data
            
        except instaloader.exceptions.ProfileNotExistsException:
            print(f"❌ Profile @{username} does not exist")
            return None
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            print(f"🔒 Profile @{username} is private and we don't follow them")
            return None
        except instaloader.exceptions.LoginRequiredException:
            print("🔒 Login required to view this profile. Please provide Instagram credentials.")
            return None
        except Exception as e:
            print(f"❌ Error fetching profile: {str(e)}")
            print("⚠️  Some features may not be available due to API limitations.")
            return None
    
    def analyze_profile(self, username: str):
        """
        Analyze an Instagram profile and display results.
        
        Args:
            username: Instagram username (with or without @)
        """
        # Get profile data
        profile = self.get_profile(username)
        if not profile:
            return
        
        # Display profile information
        self._display_profile_info(profile)
        
        # Prepare data for the detector
        detector_data = {
            'name': profile['full_name'],
            'screen_name': profile['username'],
            'description': profile['biography'],
            'statuses_count': profile['posts'],
            'followers_count': profile['followers'],
            'friends_count': profile['followees'],
            'favourites_count': 0,  # Not available in Instagram
            'listed_count': 0,  # Not available in Instagram
            'verified': profile['is_verified'],
            'default_profile': int(not profile['has_profile_pic']),
            'default_profile_image': int(profile['has_default_profile_pic']),
            'geo_enabled': 0,  # Not available in Instagram
            'created_at': profile['created_at'],
            'url': profile['external_url'],
            'engagement_rate': profile['engagement_rate'],
            'is_private': profile['is_private'],
            'is_business': profile['is_business_account']
        }
        
        # Make prediction
        result = self.detector.predict(detector_data)
        
        # Display analysis results
        self._display_analysis_results(result, profile)
    
    def _display_profile_info(self, profile: dict):
        """Display Instagram profile information."""
        print("\n" + "="*60)
        print(f"📷 @{profile['username']}")
        if profile['full_name']:
            print(f"👤 {profile['full_name']}")
        
        if profile['is_verified']:
            print("✅ Verified Account")
        
        if profile['is_private']:
            print("🔒 Private Account")
        
        if profile['is_business_account'] and profile['business_category']:
            print(f"🏢 Business Account: {profile['business_category']}")
        
        print("\n📝 Bio:" if profile['biography'] else "\n📝 No bio")
        if profile['biography']:
            print(profile['biography'])
        
        if profile['external_url']:
            print(f"\n🔗 {profile['external_url']}")
        
        print("\n📊 Stats:")
        print(f"  • Posts: {profile['posts']:,}")
        print(f"  • Followers: {profile['followers']:,}")
        print(f"  • Following: {profile['followees']:,}")
        
        if profile['account_age_days'] > 0:
            years = profile['account_age_days'] / 365.25
            print(f"  • Account Age: {int(years)} years ({profile['account_age_days']} days)")
        
        if profile['engagement_rate'] > 0:
            print(f"  • Engagement Rate: {profile['engagement_rate']:.2f}%")
        
        if profile['recent_posts_count'] > 0:
            print(f"  • Avg. Likes (recent): {int(profile['avg_likes']):,}")
            print(f"  • Avg. Comments (recent): {int(profile['avg_comments']):,}")
        
        if profile['recent_hashtags']:
            print(f"\n🏷️  Recent Hashtags: {' '.join('#' + tag for tag in profile['recent_hashtags'][:10])}")
            if len(profile['recent_hashtags']) > 10:
                print(f"   ... and {len(profile['recent_hashtags']) - 10} more")
        
        print("="*60)
    
    def _display_analysis_results(self, result: dict, profile: dict):
        """Display the analysis results."""
        if 'error' in result:
            print(f"\n❌ Error during analysis: {result['error']}")
            return
        
        print("\n🔍 Profile Analysis Results:")
        print("-" * 50)
        
        # Display prediction
        if result['is_fake']:
            confidence = result.get('confidence', 0)
            print(f"⚠️  Potential Fake Profile ({confidence:.1f}% confidence)")
        else:
            confidence = 100 - result.get('confidence', 0)
            print(f"✅ Likely Genuine Profile ({confidence:.1f}% confidence)")
        
        # Display risk factors
        if result.get('negative_indicators'):
            print("\n🔍 Risk Factors:")
            for factor in result['negative_indicators']:
                print(f"  • {factor}")
                
        # Display positive indicators
        if result.get('positive_indicators'):
            print("\n✅ Positive Indicators:")
            for factor in result['positive_indicators']:
                print(f"  • {factor}")
        
        # Display key indicators
        print("\n🔍 Key Indicators:")
        
        # Positive indicators (genuine)
        positive = []
        if profile['is_verified']:
            positive.append("Verified account")
        if profile['posts'] > 100:
            positive.append(f"Active user ({profile['posts']} posts)")
        if profile['engagement_rate'] > 5:  # Above average engagement
            positive.append(f"Good engagement rate ({profile['engagement_rate']:.1f}%)")
        if profile['account_age_days'] > 365:
            positive.append(f"Old account ({profile['account_age_days']} days)")
        
        # Negative indicators (fake)
        negative = []
        if profile.get('has_default_profile_pic', False):
            negative.append("Default profile picture")

        # Combine all indicators
        result = {
            'is_fake': len(negative) > len(positive),
            'confidence': min(100, len(negative) * 15),  # 15% per negative indicator
            'reasons': negative + positive,
            'positive_indicators': positive,
            'negative_indicators': negative
        }
        
        return result


def main():
    """Main interactive function."""
    print("\n" + "="*60)
    print("📷 Instagram Profile Analyzer - Fake Profile Detection")
    print("Enter an Instagram username to analyze (or 'q' to quit)")
    print("Example: zuck or @zuck")
    print("="*60)
    
    analyzer = InstagramAnalyzer()
    
    while True:
        username = input("\nEnter Instagram username: ").strip()
        
        if username.lower() in ['q', 'quit', 'exit']:
            print("Goodbye! 👋")
            break
            
        if not username:
            print("Please enter a username.")
            continue
            
        analyzer.analyze_profile(username)

if __name__ == "__main__":
    main()
