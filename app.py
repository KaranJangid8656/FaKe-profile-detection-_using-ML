from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_from_directory
import pandas as pd
import joblib
import os
import sys
import logging
from pathlib import Path
from whitelist import is_whitelisted
from instagram_analyzer import InstagramAnalyzer
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Constants
MODEL_PATH = Path('saved_model/random_forest_model.pkl')
REQUIRED_FEATURES = [
    'followers_count', 'following_count', 'post_count',
    'has_profile_pic', 'is_private', 'is_verified'
]

# Initialize model and related data
model = None
feature_columns = []
lang_dict = {}

def load_model():
    """Load the trained model and related data"""
    global model, feature_columns, lang_dict
    try:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        model_data = joblib.load(MODEL_PATH)
        model = model_data.get('model')
        feature_columns = model_data.get('feature_columns', [])
        lang_dict = model_data.get('lang_dict', {})
        if model is None:
            raise ValueError("Model not found in the loaded data")
        logger.info("Successfully loaded model and related data")
        return True
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return False

def predict_gender(name):
    """Predict gender from name using simple heuristics
    Args:
        name (str): The full name to analyze
    Returns:
        int: -1 for female, 1 for male, 0 for unknown
    """
    if not name or not isinstance(name, str):
        return 0
    first_name = name.split(' ')[0].lower()
    female_endings = ['a', 'e', 'i', 'y']
    male_endings = ['o', 'r', 's', 't', 'n']
    if any(first_name.endswith(ending) for ending in female_endings):
        return -1  # female
    elif any(first_name.endswith(ending) for ending in male_endings):
        return 1   # male
    return 0       # unknown

# Initialize Instagram analyzer
analyzer = InstagramAnalyzer()

@app.route('/')
def home():
    """Redirect to the Instagram analyzer page"""
    return redirect(url_for('instagram_analyzer'))

# Whitelist is now managed in whitelist.py
def validate_input_data(data):
    """Validate the input data for prediction
    Args:
        data (dict): Dictionary containing form data
    Returns:
        tuple: (is_valid, error_message, validated_data)
    """
    validated = {}
    # Required fields check
    for field in REQUIRED_FEATURES:
        if field not in data:
            return False, f"Missing required field: {field}", None
    # Type conversion and validation
    try:
        # Numeric fields
        for field in ['followers_count', 'following_count', 'post_count']:
            validated[field] = int(data[field])
            if validated[field] < 0:
                return False, f"{field} cannot be negative", None
        # Boolean fields
        for field in ['has_profile_pic', 'is_private', 'is_verified']:
            val = str(data[field]).lower()
            if val in ['true', '1', 'yes', 'y']:
                validated[field] = True
            elif val in ['false', '0', 'no', 'n']:
                validated[field] = False
            else:
                return False, f"Invalid boolean value for {field}: {data[field]}", None
        return True, "", validated
    except ValueError as e:
        return False, f"Invalid input format: {str(e)}", None

@app.route('/predict', methods=['POST'])
def predict():
    """Handle prediction requests"""
    try:
        if model is None:
            logger.error("Model not loaded")
            return jsonify({
                'status': 'error',
                'message': 'Prediction model is not available. Please try again later.'
            }), 503  # Service Unavailable
        
        data = request.form.to_dict()
        user_id = data.get('user_id', '').strip()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
            
        # Check whitelist
        if is_whitelisted(user_id):
            logger.info(f"User {user_id} is in whitelist")
            return render_template('result.html', 
                               result={
                                   'prediction': 'GENUINE',
                                   'confidence': 99.9,
                                   'is_whitelisted': True,
                                   'features': {
                                       'statuses_count': 0,
                                       'followers_count': 0,
                                       'friends_count': 0
                                   }
                               },
                               request=request)
        
        # Extract and validate features
        features = {
            'followers_count': int(data.get('followers_count', 0)),
            'following_count': int(data.get('following_count', 0)),
            'post_count': int(data.get('post_count', 0)),
            'has_profile_pic': 1 if data.get('has_profile_pic', 'true').lower() == 'true' else 0,
            'is_private': 1 if data.get('is_private', 'false').lower() == 'true' else 0,
            'is_verified': 1 if data.get('is_verified', 'false').lower() == 'true' else 0,
            'lang_code': lang_dict.get(data.get('language', 'en').lower(), 0)
        }
        
        # Heuristic checks for suspicious profiles
        is_suspicious = False
        
        # Check for suspicious following/follower ratio (only for non-verified accounts)
        if not features['is_verified'] and features['followers_count'] > 0 and features['following_count'] / features['followers_count'] < 0.01:
            is_suspicious = True
            logger.info(f"Suspicious following/follower ratio for user {user_id}")
            
        # Check for very low post count relative to followers (only for non-verified accounts)
        if not features['is_verified'] and features['followers_count'] > 1000 and features['post_count'] < 10:
            is_suspicious = True
            logger.info(f"Suspiciously low post count for user {user_id}")
            
        # Check for private account with high follower count (only for non-verified accounts)
        if not features['is_verified'] and features['is_private'] and features['followers_count'] > 5000:
            is_suspicious = True
            logger.info(f"Suspicious private account with high follower count for user {user_id}")
            
        # Influencer check - verified accounts with high follower count
        is_influencer = features['is_verified'] and features['followers_count'] > 10000
        
        # If influencer, mark as genuine regardless of other checks
        if is_influencer:
            logger.info(f"Influencer profile detected for user {user_id}")
            return render_template('result.html',
                               result={
                                   'prediction': 'GENUINE',
                                   'confidence': 99.0,
                                   'is_whitelisted': False,
                                   'is_influencer': True,
                                   'features': {
                                       'statuses_count': features['post_count'],
                                       'followers_count': features['followers_count'],
                                       'friends_count': features['following_count']
                                   }
                               },
                               request=request)
            
        # If any suspicious flags are raised and not an influencer, mark as fake
        if is_suspicious:
            return render_template('result.html',
                               result={
                                   'prediction': 'FAKE',
                                   'confidence': 95.0,
                                   'is_whitelisted': False,
                                   'features': {
                                       'statuses_count': features['post_count'],
                                       'followers_count': features['followers_count'],
                                       'friends_count': features['following_count']
                                   }
                               },
                               request=request)
        is_valid, error_msg, validated_data = validate_input_data(features)
        if not is_valid:
            logger.warning(f"Invalid input data: {error_msg}")
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
        df = pd.DataFrame([validated_data])
        for col in feature_columns:
            if col not in df.columns:
                df[col] = 0  # Fill missing columns with default value
        df = df[feature_columns]
        prediction = model.predict(df)[0]
        proba = model.predict_proba(df)[0]
        confidence = max(proba) * 100
        label = 'GENUINE' if prediction == 1 else 'FAKE'
        logger.info(f"Prediction for user {user_id}: {label} (confidence: {confidence:.2f}%)")
        return render_template('result.html', 
                               result={
                                   'prediction': label,
                                   'confidence': round(confidence, 2),
                                   'is_whitelisted': False,
                                   'features': {
                                       'statuses_count': validated_data.get('statuses_count', 0),
                                       'followers_count': validated_data.get('followers_count', 0),
                                       'friends_count': validated_data.get('friends_count', 0)
                                   }
                               },
                               request=request)
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during prediction',
            'details': str(e)
        }), 500

def init_app():
    """Initialize the Flask application"""
    os.makedirs('templates', exist_ok=True)
    os.makedirs('saved_model', exist_ok=True)
    if not load_model():
        logger.warning("Failed to load model on startup. Will try lazy loading.")

@app.route('/proxy-image', methods=['GET'])
def proxy_image():
    """Proxy Instagram images to avoid CORS issues."""
    import requests
    from flask import Response, request
    from urllib.parse import unquote
    import base64
    import hashlib
    import os
    
    logger.info(f"🔍 Proxy image endpoint called. Method: {request.method}, Args: {dict(request.args)}")
    
    try:
        # Get URL from query parameter
        image_url = request.args.get('url')
        
        logger.info(f"🔍 Raw image_url from args: {image_url[:100] if image_url else 'None'}...")
        
        if not image_url or image_url.strip() == '':
            logger.warning("⚠️ No image URL provided to proxy")
            return _get_placeholder_image()
        
        # Decode URL if needed
        image_url = unquote(image_url).strip()
        
        logger.info(f"Decoded image URL: {image_url[:150]}...")
        
        # Validate URL
        if not image_url.startswith('http'):
            logger.warning(f"Invalid image URL (doesn't start with http): {image_url[:100]}...")
            return _get_placeholder_image()
        
        logger.info(f"Fetching image from: {image_url[:150]}...")
        
        # Create cache directory
        cache_dir = Path('static') / 'profile_images'
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create cache key from URL
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        cache_file = cache_dir / f"{url_hash}.jpg"
        
        # Check cache first
        if cache_file.exists():
            logger.info(f"Serving cached image: {cache_file}")
            with open(cache_file, 'rb') as f:
                return Response(f.read(), 
                              mimetype='image/jpeg',
                              headers={
                                  'Cache-Control': 'public, max-age=86400',
                                  'Access-Control-Allow-Origin': '*'
                              })
        
        # Add proper headers for Instagram CDN requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.instagram.com/',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site'
        }
        
        # Fetch the image with proper headers
        response = requests.get(image_url, headers=headers, timeout=15, allow_redirects=True, stream=True)
        
        logger.info(f"Image fetch response status: {response.status_code}")
        
        if response.status_code == 200:
            # Get image content
            image_content = response.content
            
            # Determine content type
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            if 'image' not in content_type:
                content_type = 'image/jpeg'
            
            # Cache the image
            try:
                with open(cache_file, 'wb') as f:
                    f.write(image_content)
                logger.info(f"Cached image: {cache_file}")
            except Exception as cache_error:
                logger.warning(f"Failed to cache image: {cache_error}")
            
            logger.info(f"Successfully fetched image, size: {len(image_content)} bytes, type: {content_type}")
            
            # Return the image with appropriate headers
            return Response(image_content, 
                          mimetype=content_type,
                          headers={
                              'Cache-Control': 'public, max-age=86400',
                              'Access-Control-Allow-Origin': '*',
                              'Content-Type': content_type
                          })
        else:
            logger.warning(f"Failed to fetch image: {response.status_code}")
            # Return placeholder if image fetch fails
            return _get_placeholder_image()
    except requests.exceptions.Timeout:
        logger.error("Timeout while fetching image")
        return _get_placeholder_image()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error proxying image: {str(e)}")
        return _get_placeholder_image()
    except Exception as e:
        logger.error(f"Error proxying image: {str(e)}", exc_info=True)
        return _get_placeholder_image()

def _get_placeholder_image():
    """Get a placeholder image."""
    import requests
    from flask import Response
    try:
        placeholder_url = 'https://via.placeholder.com/150/cccccc/666666?text=No+Image'
        placeholder_response = requests.get(placeholder_url, timeout=5)
        return Response(placeholder_response.content, 
                      mimetype='image/png',
                      headers={
                          'Cache-Control': 'public, max-age=3600',
                          'Access-Control-Allow-Origin': '*'
                      })
    except:
        # Last resort: return a simple 1x1 transparent pixel
        from base64 import b64decode
        transparent_pixel = b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        return Response(transparent_pixel, 
                      mimetype='image/gif',
                      headers={
                          'Cache-Control': 'public, max-age=3600',
                          'Access-Control-Allow-Origin': '*'
                      })

@app.route('/instagram')
def instagram_analyzer():
    """Render the Instagram analyzer page."""
    return render_template('instagram.html')

@app.route('/api/analyze/instagram', methods=['POST'])
def analyze_instagram():
    """Analyze Instagram profile."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip('@')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        # Get profile data
        profile = analyzer.get_profile(username)
        
        if profile is None:
            return jsonify({
                'error': 'Instagram is temporarily rate-limiting requests. Please wait a few minutes and try again.',
                'error_type': 'rate_limit',
                'retry_after': '5-10 minutes'
            }), 429
        
        # Make prediction
        print("✅ Profile data received successfully")
        
        # Log profile image URL for debugging
        profile_pic_url = profile.get('profile_pic_url', '')
        has_profile_pic = profile.get('has_profile_pic', False)
        
        print(f"🔍 Debug - Profile pic URL: {profile_pic_url[:100] if profile_pic_url else 'NOT FOUND'}...")
        print(f"🔍 Debug - Has profile pic flag: {has_profile_pic}")
        print(f"🔍 Debug - URL length: {len(profile_pic_url) if profile_pic_url else 0}")
        
        # Ensure profile_pic_url is set (even if empty)
        if 'profile_pic_url' not in profile:
            profile['profile_pic_url'] = ''
        
        # If has_profile_pic is True but URL is empty, try to get it from Instagram
        if has_profile_pic and not profile_pic_url:
            print("⚠️  Profile has pic flag but no URL - attempting to fetch...")
            try:
                # Try to get fresh profile data
                fresh_profile = analyzer._try_instaloader_original(username)
                if fresh_profile and fresh_profile.get('profile_pic_url'):
                    profile['profile_pic_url'] = fresh_profile['profile_pic_url']
                    print(f"✅ Retrieved profile pic URL: {profile['profile_pic_url'][:100]}...")
            except Exception as e:
                print(f"⚠️  Could not fetch profile pic URL: {e}")
        
        # Ensure has_profile_pic matches reality
        if profile.get('profile_pic_url') and profile['profile_pic_url'].strip():
            profile['has_profile_pic'] = True
        elif not profile.get('profile_pic_url') or not profile['profile_pic_url'].strip():
            profile['has_profile_pic'] = False
        
        # Make prediction using the detector
        print("🤖 Making prediction...")
        prediction = analyzer.detector.predict(profile)
        
        print(f"🔍 Debug - Profile total_posts: {profile.get('total_posts', 'NOT FOUND')}")
        print(f"🔍 Debug - Prediction confidence: {prediction.get('confidence', 'NOT FOUND')}")
        
        return jsonify({
            'success': True, 
            'profile': profile,
            'analysis': prediction
        })
            
    except Exception as e:
        print(f"❌ Flask route error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/test/instagram', methods=['GET'])
def test_instagram():
    """Test endpoint to verify Instagram functionality."""
    try:
        print("🧪 Testing Instagram connection...")
        analyzer = InstagramAnalyzer()
        profile = analyzer.get_profile('instagram')
        
        if profile:
            return jsonify({
                'success': True,
                'test_profile': {
                    'username': profile.get('username'),
                    'followers': profile.get('followers'),
                    'following': profile.get('following'),
                    'posts': profile.get('total_posts'),
                    'profile_pic_url': profile.get('profile_pic_url', ''),
                    'has_profile_pic': profile.get('has_profile_pic', False)
                }
            })
        else:
            return jsonify({'error': 'Test failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/image')
def test_image():
    """Test endpoint to verify image proxy functionality."""
    from flask import request
    test_url = request.args.get('url', 'https://via.placeholder.com/150')
    
    try:
        import requests
        response = requests.get(test_url, timeout=10)
        return jsonify({
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'content_type': response.headers.get('Content-Type'),
            'content_length': len(response.content) if response.status_code == 200 else 0
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-proxy')
def test_proxy():
    """Test the proxy endpoint with a known good image."""
    test_image_url = 'https://via.placeholder.com/150/cccccc/666666?text=Test+Image'
    return redirect(f'/proxy-image?url={test_image_url}')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
