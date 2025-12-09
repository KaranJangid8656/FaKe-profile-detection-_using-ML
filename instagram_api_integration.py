"""
Instagram API Integration for Real Data Fetching
Supports multiple API methods and proxy rotation
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional

class InstagramAPIIntegration:
    def __init__(self):
        self.access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
        self.app_id = os.getenv('INSTAGRAM_APP_ID', '')
        self.app_secret = os.getenv('INSTAGRAM_APP_SECRET', '')
        
        # Proxy list for rotation
        self.proxies = [
            # Add your proxies here in format: "http://ip:port" or "https://user:pass@ip:port"
            # Example: "http://proxy1.example.com:8080"
        ]
        
        # API endpoints
        self.graph_api_url = "https://graph.instagram.com"
        self.basic_display_url = "https://api.instagram.com"
    
    def get_profile_real_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get real Instagram profile data using multiple API methods."""
        print(f"🔍 Fetching REAL data for @{username}...")
        
        # Method 1: Try Instagram Basic Display API
        if self.access_token:
            profile_data = self._try_basic_display_api(username)
            if profile_data:
                return profile_data
        
        # Method 2: Try Graph API with app access
        if self.app_id and self.app_secret:
            profile_data = self._try_graph_api(username)
            if profile_data:
                return profile_data
        
        # Method 3: Try public API endpoints
        profile_data = self._try_public_apis(username)
        if profile_data:
            return profile_data
        
        # Method 4: Advanced scraping with proxy rotation
        profile_data = self._try_proxy_scraping(username)
        if profile_data:
            return profile_data
        
        print("❌ All real data methods failed")
        return None
    
    def _try_basic_display_api(self, username: str) -> Optional[Dict[str, Any]]:
        """Try Instagram Basic Display API."""
        try:
            print("🔄 Trying Basic Display API...")
            
            # Get user ID from username
            url = f"{self.basic_display_url}/v1/users/search"
            params = {
                'q': username,
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                users = response.json().get('data', [])
                for user in users:
                    if user.get('username', '').lower() == username.lower():
                        user_id = user['id']
                        
                        # Get user details
                        details_url = f"{self.basic_display_url}/v1/users/{user_id}"
                        details_params = {
                            'fields': 'id,username,account_type,media_count,followers_count,follows_count,biography,profile_picture_url',
                            'access_token': self.access_token
                        }
                        
                        details_response = requests.get(details_url, params=details_params, timeout=10)
                        
                        if details_response.status_code == 200:
                            user_data = details_response.json()
                            followers = user_data.get('followers_count', 0)
                            following = user_data.get('follows_count', 0)
                            posts = user_data.get('media_count', 0)
                            
                            print(f"✅ Basic Display API success: {followers:,} followers, {following:,} following, {posts:,} posts")
                            
                            return {
                                'username': user_data.get('username', username),
                                'followers': followers,
                                'following': following,
                                'total_posts': posts,
                                'is_verified': user_data.get('account_type') == 'BUSINESS',
                                'is_private': user_data.get('account_type') == 'PRIVATE',
                                'has_profile_pic': bool(user_data.get('profile_picture_url', '')),
                                'biography': user_data.get('biography', ''),
                                'account_age_days': 365,
                                'profile_pic_url': user_data.get('profile_picture_url', ''),
                                'scraped': True,
                                'method': 'basic_display_api'
                            }
            
        except Exception as e:
            print(f"❌ Basic Display API error: {str(e)[:50]}...")
        
        return None
    
    def _try_graph_api(self, username: str) -> Optional[Dict[str, Any]]:
        """Try Facebook Graph API."""
        try:
            print("🔄 Trying Graph API...")
            
            # Get app access token
            token_url = f"https://graph.facebook.com/oauth/access_token"
            token_params = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'grant_type': 'client_credentials'
            }
            
            response = requests.get(token_url, params=token_params, timeout=10)
            
            if response.status_code == 200:
                app_token = response.json().get('access_token')
                
                # Search for user
                search_url = f"https://graph.facebook.com/instagram_oembed"
                search_params = {
                    'url': f"https://www.instagram.com/{username}/",
                    'access_token': app_token
                }
                
                search_response = requests.get(search_url, params=search_params, timeout=10)
                
                if search_response.status_code == 200:
                    data = search_response.json()
                    
                    # Extract available data
                    author_name = data.get('author_name', username)
                    author_url = data.get('author_url', '')
                    
                    print(f"✅ Graph API partial success: @{author_name}")
                    
                    return {
                        'username': author_name,
                        'followers': 0,  # Not available from this endpoint
                        'following': 0,
                        'total_posts': 0,
                        'is_verified': False,
                        'is_private': False,
                        'has_profile_pic': True,
                        'biography': 'Profile found via Graph API',
                        'account_age_days': 365,
                        'profile_pic_url': '',
                        'scraped': True,
                        'method': 'graph_api_partial',
                        'note': 'Partial data from Graph API'
                    }
            
        except Exception as e:
            print(f"❌ Graph API error: {str(e)[:50]}...")
        
        return None
    
    def _try_public_apis(self, username: str) -> Optional[Dict[str, Any]]:
        """Try various public API endpoints."""
        try:
            print("🔄 Trying public APIs...")
            
            # Try multiple public endpoints
            endpoints = [
                f"https://nitter.net/{username}/rss",  # Alternative frontend
                f"https://r.jina.ai/http://instagram.com/{username}",  # Jina AI scraper
                f"https://r.jina.ai/http://www.instagram.com/{username}",  # Alternative Jina
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Parse content for follower counts
                        import re
                        follower_patterns = [
                            r'(\d+(?:,\d+)*)\s*followers',
                            r'(\d+(?:,\d+)*)\s*Followers',
                            r'"followers":\s*(\d+)',
                            r'followerCount["\s]*:["\s]*(\d+)',
                        ]
                        
                        for pattern in follower_patterns:
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                followers = int(match.group(1).replace(',', ''))
                                
                                print(f"✅ Public API success: {followers:,} followers")
                                
                                return {
                                    'username': username,
                                    'followers': followers,
                                    'following': 0,
                                    'total_posts': 0,
                                    'is_verified': False,
                                    'is_private': False,
                                    'has_profile_pic': True,
                                    'biography': 'Data from public API',
                                    'account_age_days': 365,
                                    'profile_pic_url': '',
                                    'scraped': True,
                                    'method': 'public_api',
                                    'note': 'Partial data from public API'
                                }
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"❌ Public APIs error: {str(e)[:50]}...")
        
        return None
    
    def _try_proxy_scraping(self, username: str) -> Optional[Dict[str, Any]]:
        """Try scraping with proxy rotation."""
        try:
            print("🔄 Trying proxy scraping...")
            
            # List of user agents to rotate
            user_agents = [
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/109.0 Firefox/115.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            
            for i, user_agent in enumerate(user_agents):
                try:
                    headers = {
                        'User-Agent': user_agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                    }
                    
                    proxies = {}
                    if self.proxies:
                        proxies = {
                            'http': self.proxies[i % len(self.proxies)],
                            'https': self.proxies[i % len(self.proxies)]
                        }
                    
                    url = f"https://www.instagram.com/{username}/"
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
                    
                    if response.status_code == 200:
                        # Parse HTML for data
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for meta description
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if meta_desc and meta_desc.get('content'):
                            content = meta_desc['content']
                            
                            # Extract follower counts
                            import re
                            follower_match = re.search(r'(\d+(?:,\d+)*)\s*Followers?', content)
                            following_match = re.search(r'(\d+(?:,\d+)*)\s*Following?', content)
                            post_match = re.search(r'(\d+(?:,\d+)*)\s*Posts?', content)
                            
                            if follower_match:
                                followers = int(follower_match.group(1).replace(',', ''))
                                following = int(following_match.group(1).replace(',', '')) if following_match else 0
                                posts = int(post_match.group(1).replace(',', '')) if post_match else 0
                                
                                print(f"✅ Proxy scraping success: {followers:,} followers, {following:,} following, {posts:,} posts")
                                
                                return {
                                    'username': username,
                                    'followers': followers,
                                    'following': following,
                                    'total_posts': posts,
                                    'is_verified': False,
                                    'is_private': False,
                                    'has_profile_pic': True,
                                    'biography': content,
                                    'account_age_days': 365,
                                    'profile_pic_url': '',
                                    'scraped': True,
                                    'method': 'proxy_scraping'
                                }
                    
                    elif response.status_code == 429:
                        print(f"⏰ Rate limited on proxy {i+1}")
                        continue
                    
                    time.sleep(1)  # Delay between attempts
                    
                except Exception as e:
                    print(f"❌ Proxy {i+1} failed: {str(e)[:50]}...")
                    continue
            
        except Exception as e:
            print(f"❌ Proxy scraping error: {str(e)[:50]}...")
        
        return None
    
    def setup_api_credentials(self, access_token: str = "", app_id: str = "", app_secret: str = ""):
        """Setup API credentials for real data access."""
        if access_token:
            self.access_token = access_token
            print("✅ Access token configured")
        
        if app_id:
            self.app_id = app_id
            print("✅ App ID configured")
        
        if app_secret:
            self.app_secret = app_secret
            print("✅ App secret configured")
        
        # Save to environment
        if access_token:
            os.environ['INSTAGRAM_ACCESS_TOKEN'] = access_token
        if app_id:
            os.environ['INSTAGRAM_APP_ID'] = app_id
        if app_secret:
            os.environ['INSTAGRAM_APP_SECRET'] = app_secret
    
    def add_proxy(self, proxy_url: str):
        """Add a proxy to the rotation list."""
        self.proxies.append(proxy_url)
        print(f"✅ Added proxy: {proxy_url}")
    
    def get_setup_instructions(self):
        """Return setup instructions for real API access."""
        instructions = """
🔧 SETUP INSTRUCTIONS FOR REAL INSTAGRAM DATA:

1. INSTAGRAM BASIC DISPLAY API:
   - Go to https://developers.facebook.com/
   - Create a new app and add Instagram Basic Display
   - Get your Access Token
   - Run: api.setup_api_credentials(access_token="YOUR_TOKEN")

2. FACEBOOK GRAPH API:
   - Get App ID and App Secret from Facebook Developers
   - Run: api.setup_api_credentials(app_id="YOUR_ID", app_secret="YOUR_SECRET")

3. PROXY ROTATION:
   - Add proxies to bypass rate limits
   - Run: api.add_proxy("http://proxy_ip:port")

4. ENVIRONMENT VARIABLES:
   - Set in .env file:
     INSTAGRAM_ACCESS_TOKEN=your_token
     INSTAGRAM_APP_ID=your_app_id  
     INSTAGRAM_APP_SECRET=your_app_secret

5. ALTERNATIVE: Use third-party services:
   - RapidAPI Instagram endpoints
   - ScrapeOps API
   - ZenRows API
   - Bright Data API
        """
        return instructions.strip()
