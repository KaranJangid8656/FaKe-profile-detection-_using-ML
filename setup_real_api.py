#!/usr/bin/env python3
"""
Setup script for real Instagram API integration
Run this to configure real data fetching
"""

import os
from instagram_api_integration import InstagramAPIIntegration

def main():
    print("🔧 INSTAGRAM REAL API SETUP")
    print("=" * 50)
    
    api = InstagramAPIIntegration()
    
    print("\n📋 Choose API Setup Method:")
    print("1. Instagram Basic Display API (Recommended)")
    print("2. Facebook Graph API")
    print("3. Third-party API (RapidAPI, etc.)")
    print("4. Add Proxy Servers")
    print("5. Show setup instructions")
    print("6. Test current configuration")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        print("\n📱 INSTAGRAM BASIC DISPLAY API SETUP")
        print("-" * 40)
        print("Steps:")
        print("1. Go to https://developers.facebook.com/")
        print("2. Create new app > Add Instagram Basic Display")
        print("3. Get your Access Token")
        print("4. Enter it below:")
        
        access_token = input("Access Token: ").strip()
        if access_token:
            api.setup_api_credentials(access_token=access_token)
            print("✅ Basic Display API configured!")
        else:
            print("❌ No token provided")
    
    elif choice == "2":
        print("\n🌐 FACEBOOK GRAPH API SETUP")
        print("-" * 40)
        print("Steps:")
        print("1. Go to Facebook Developers Dashboard")
        print("2. Get your App ID and App Secret")
        print("3. Enter them below:")
        
        app_id = input("App ID: ").strip()
        app_secret = input("App Secret: ").strip()
        
        if app_id and app_secret:
            api.setup_api_credentials(app_id=app_id, app_secret=app_secret)
            print("✅ Graph API configured!")
        else:
            print("❌ Missing credentials")
    
    elif choice == "3":
        print("\n🔌 THIRD-PARTY API SETUP")
        print("-" * 40)
        print("Popular options:")
        print("1. RapidAPI - Instagram API")
        print("2. ScrapeOps - Web scraping API")
        print("3. ZenRows - Advanced scraping")
        print("4. Bright Data - Data collection")
        print("\nThese require API keys from respective services.")
        print("Configure them in environment variables or .env file")
        
        api_key = input("Enter API key (if available): ").strip()
        if api_key:
            # Save to .env file
            env_file = ".env"
            with open(env_file, 'a') as f:
                f.write(f"\nTHIRD_PARTY_API_KEY={api_key}")
            print(f"✅ API key saved to {env_file}")
    
    elif choice == "4":
        print("\n🔄 PROXY SERVER SETUP")
        print("-" * 40)
        print("Add proxies to bypass rate limits:")
        print("Format: http://ip:port or http://user:pass@ip:port")
        
        while True:
            proxy = input("Enter proxy (or press Enter to finish): ").strip()
            if not proxy:
                break
            api.add_proxy(proxy)
        
        print("✅ Proxies configured!")
    
    elif choice == "5":
        print("\n📖 DETAILED SETUP INSTRUCTIONS")
        print("-" * 40)
        print(api.get_setup_instructions())
    
    elif choice == "6":
        print("\n🧪 TESTING CURRENT CONFIGURATION")
        print("-" * 40)
        
        test_username = input("Enter username to test (e.g., 'instagram'): ").strip()
        if test_username:
            profile_data = api.get_profile_real_data(test_username)
            if profile_data:
                print("✅ SUCCESS! Real data retrieved:")
                print(f"   Username: {profile_data.get('username')}")
                print(f"   Followers: {profile_data.get('followers', 0):,}")
                print(f"   Following: {profile_data.get('following', 0):,}")
                print(f"   Posts: {profile_data.get('total_posts', 0):,}")
                print(f"   Method: {profile_data.get('method')}")
            else:
                print("❌ Failed to get real data")
                print("Try configuring API credentials first")
    
    else:
        print("❌ Invalid choice")
    
    print("\n🎉 Setup complete! Restart the app to use real API integration.")

if __name__ == "__main__":
    main()
