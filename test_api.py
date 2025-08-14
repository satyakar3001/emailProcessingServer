#!/usr/bin/env python3
"""
API Testing Script for Email Processor FastAPI Server
Run this script to test all endpoints
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, params=None):
    """Test an API endpoint and return the response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, data=data, params=params)
        else:
            print(f"Unsupported method: {method}")
            return None
        
        print(f"{method} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)}")
            except:
                print(f"   Response: {response.text}")
        else:
            print(f"   Error: {response.text}")
        
        print()
        return response
        
    except requests.exceptions.ConnectionError:
        print(f"Connection failed: {endpoint}")
        print("   Make sure the server is running on http://localhost:8000")
        print()
        return None
    except Exception as e:
        print(f"Error testing {endpoint}: {e}")
        print()
        return None

def main():
    """Main testing function"""
    print("Testing Email Processor API")
    print("=" * 50)
    
    # Test 1: Health Check
    print("1. Testing Health Check")
    test_endpoint("GET", "/health")
    
    # Test 2: Root endpoint
    print("2. Testing Root Endpoint")
    test_endpoint("GET", "/")
    
    # Test 3: Generate Sample Emails
    print("3. Testing Sample Email Generation")
    test_endpoint("POST", "/emails/generate-sample", params={"count": 5})
    
    # Wait a bit for processing
    print("Waiting 3 seconds for email processing...")
    time.sleep(3)
    
    # Test 4: Get Email Statistics
    print("4. Testing Email Statistics")
    test_endpoint("GET", "/emails/stats/summary")
    
    # Test 5: List Emails
    print("5. Testing Email Listing")
    test_endpoint("GET", "/emails", params={"limit": 5})
    
    # Test 6: Get Problem Emails Only
    print("6. Testing Problem Email Filtering")
    test_endpoint("GET", "/emails", params={"is_problem": "true", "limit": 3})
    
    # Test 7: Test Email Classification
    print("7. Testing Email Classification")
    test_data = {
        "subject": "Critical System Error",
        "content": "The database server is down and users cannot access the application. This is affecting all services."
    }
    test_endpoint("POST", "/emails/classify", data=test_data)
    
    # Test 8: Scheduler Status
    print("8. Testing Scheduler Status")
    test_endpoint("GET", "/scheduler/status")
    
    # Test 9: Manual Email Processing
    print("9. Testing Manual Email Processing")
    test_endpoint("POST", "/emails/process/manual")
    
    # Wait for processing
    print("Waiting 5 seconds for manual processing...")
    time.sleep(5)
    
    # Test 10: Updated Statistics
    print("10. Testing Updated Statistics")
    test_endpoint("GET", "/emails/stats/summary")
    
    print("API Testing Complete!")
    print("\nSummary:")
    print("- Health check should show 'healthy' status")
    print("- Sample emails should be generated and stored")
    print("- Statistics should show email counts")
    print("- Classification should work for test emails")
    print("- Scheduler should be running")

if __name__ == "__main__":
    main()
