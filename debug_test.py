#!/usr/bin/env python3
"""
Debug script to test Instagram functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from instagram_analyzer import InstagramAnalyzer

def test_instagram():
    print("🧪 Testing Instagram functionality...")
    
    try:
        # Initialize analyzer
        analyzer = InstagramAnalyzer()
        print("✅ InstagramAnalyzer initialized")
        
        # Test with known profile
        print("📡 Testing with 'instagram' profile...")
        profile = analyzer.get_profile('instagram')
        
        if profile:
            print("✅ Success! Profile data:")
            print(f"   Username: {profile.get('username', 'N/A')}")
            print(f"   Followers: {profile.get('followers', 'N/A')}")
            print(f"   Following: {profile.get('following', 'N/A')}")
            print(f"   Posts: {profile.get('total_posts', 'N/A')}")
            return True
        else:
            print("❌ Failed to get profile data")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_instagram()
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
    sys.exit(0 if success else 1)
