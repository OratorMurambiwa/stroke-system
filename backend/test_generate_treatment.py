#!/usr/bin/env python3
"""
Test script for the new /api/generate-treatment endpoint
This script demonstrates how to use the OpenAI Chat Completions API endpoint
"""

import requests
import json
import os
from datetime import datetime

def test_generate_treatment():
    """Test the generate treatment endpoint"""
    
    # API endpoint URL (adjust if your server runs on different port)
    url = "http://localhost:8000/api/generate-treatment"
    
    # Sample patient data
    patient_data = {
        "name": "John Doe",
        "age": 65,
        "nhiss_score": 8,
        "systolic_bp": 160,
        "diastolic_bp": 95,
        "glucose": 120,
        "oxygen_saturation": 96,
        "symptoms": "Sudden onset of left-sided weakness, slurred speech, and facial droop. Patient reports difficulty walking and holding objects with left hand."
    }
    
    print("Testing /api/generate-treatment endpoint")
    print("=" * 50)
    print(f"Patient: {patient_data['name']}")
    print(f"Age: {patient_data['age']}")
    print(f"NIHSS Score: {patient_data['nhiss_score']}")
    print(f"Symptoms: {patient_data['symptoms']}")
    print("\nSending request to OpenAI API...")
    
    try:
        # Make the API request
        response = requests.post(
            url,
            json=patient_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # Allow more time for AI processing
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Treatment plan generated:")
            print("=" * 50)
            print(f"Model Used: {result.get('model_used', 'N/A')}")
            print(f"Generated At: {result.get('generated_at', 'N/A')}")
            print(f"Patient: {result.get('patient_name', 'N/A')}")
            print("\nTreatment Plan:")
            print("-" * 30)
            print(result.get('treatment_plan', 'No plan generated'))
            
        else:
            print(f"\n❌ Error: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Response text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to the server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        
    except requests.exceptions.Timeout:
        print("\n❌ Timeout Error: Request took too long to complete.")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")

def test_missing_fields():
    """Test error handling for missing fields"""
    
    url = "http://localhost:8000/api/generate-treatment"
    
    # Incomplete patient data (missing required fields)
    incomplete_data = {
        "name": "Jane Smith",
        "age": 45
        # Missing: nhiss_score, systolic_bp, diastolic_bp, glucose, oxygen_saturation, symptoms
    }
    
    print("\n\nTesting error handling with missing fields...")
    print("=" * 50)
    
    try:
        response = requests.post(url, json=incomplete_data)
        
        if response.status_code == 400:
            error_data = response.json()
            print("✅ Error handling works correctly!")
            print(f"Error message: {error_data.get('detail', 'Unknown error')}")
        else:
            print(f"❌ Expected 400 error, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing missing fields: {str(e)}")

def main():
    """Main test function"""
    print("OpenAI Chat Completions API Test")
    print("=" * 60)
    print("This script tests the new /api/generate-treatment endpoint")
    print("Make sure your FastAPI server is running and OPENAI_API_KEY is set!")
    print()
    
    # Test with complete data
    test_generate_treatment()
    
    # Test error handling
    test_missing_fields()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("\nTo use this endpoint in your application:")
    print("1. Ensure OPENAI_API_KEY is set in your environment")
    print("2. Start your FastAPI server")
    print("3. Send POST requests to /api/generate-treatment with patient data")

if __name__ == "__main__":
    main()
