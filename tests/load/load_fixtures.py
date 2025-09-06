#!/usr/bin/env python3
"""
Script to load all fixtures in the correct dependency order
"""

import subprocess
import sys

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"   Error: {e.stderr.strip()}")
        return False

def main():
    """Load fixtures in dependency order"""
    fixtures = [
        # Base data first
        "api/common/fixtures/countries.json",
        
        # Users (required by most other models)
        "api/users/fixtures/users.json",
        
        # Configuration
        "api/config/fixtures/config.json",
        
        # Stations
        "api/stations/fixtures/stations.json",
        
        # Points and Promotions
        "api/points/fixtures/points.json",
        "api/promotions/fixtures/promotions.json",
        
        # Content
        "api/content/fixtures/content.json",
    ]
    
    print("🚀 Loading fixtures in dependency order...\n")
    
    success_count = 0
    for fixture in fixtures:
        command = f"docker compose run --rm migrations python manage.py loaddata {fixture}"
        if run_command(command):
            success_count += 1
        print()  # Empty line for readability
    
    print(f"📊 Summary: {success_count}/{len(fixtures)} fixtures loaded successfully")
    
    if success_count == len(fixtures):
        print("🎉 All fixtures loaded successfully!")
        return 0
    else:
        print("⚠️  Some fixtures failed to load. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())