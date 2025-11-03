#!/usr/bin/env python3
"""
Simple test script for PLUMBUS
Tests basic functionality of the backup system
"""
import os
import sys
import tempfile
import sqlite3

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import Database

def test_database():
    """Test database operations"""
    print("🧪 Testing database operations...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Create database
        db = Database(db_path)
        print("   ✓ Database created")
        
        # Add a client
        client_id = db.add_client(
            name="Test Raspberry Pi",
            host="192.168.1.100",
            port=22,
            username="pi",
            password="testpass"
        )
        print(f"   ✓ Client added with ID: {client_id}")
        
        # Get client
        client = db.get_client(client_id)
        assert client['name'] == "Test Raspberry Pi"
        print("   ✓ Client retrieved successfully")
        
        # Add a job
        job_id = db.add_job(
            client_id=client_id,
            name="Test Backup Job",
            source_path="/home/pi",
            schedule="0 2 * * *"
        )
        print(f"   ✓ Job added with ID: {job_id}")
        
        # Get job
        job = db.get_job(job_id)
        assert job['name'] == "Test Backup Job"
        print("   ✓ Job retrieved successfully")
        
        # List all
        clients = db.get_all_clients()
        jobs = db.get_all_jobs()
        assert len(clients) == 1
        assert len(jobs) == 1
        print("   ✓ List operations work")
        
        print("✅ Database tests passed!")
        return True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from backend.database import Database
        print("   ✓ Database module imported")
        
        from backend.ssh_client import SSHClient
        print("   ✓ SSH Client module imported")
        
        from backend.backup_manager import BackupManager
        print("   ✓ Backup Manager module imported")
        
        import flask
        print("   ✓ Flask imported")
        
        import paramiko
        print("   ✓ Paramiko imported")
        
        from apscheduler.schedulers.background import BackgroundScheduler
        print("   ✓ APScheduler imported")
        
        print("✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("🧪 Testing file structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'README.md',
        'backend/__init__.py',
        'backend/database.py',
        'backend/ssh_client.py',
        'backend/backup_manager.py',
        'templates/index.html',
        'static/style.css',
        'static/app.js',
        '.github/workflows/docker-build.yml'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✓ {file}")
        else:
            print(f"   ❌ {file} missing")
            all_exist = False
    
    if all_exist:
        print("✅ All required files present!")
    else:
        print("❌ Some files are missing")
    
    return all_exist

if __name__ == '__main__':
    print("=" * 70)
    print("🛸 PLUMBUS Test Suite")
    print("   Persistent Linux Unified Multi-device Backup & Update System")
    print("=" * 70)
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Run tests
    if test_file_structure():
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    if test_imports():
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    if test_database():
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    print("=" * 70)
    print(f"Tests passed: {tests_passed}/3")
    print(f"Tests failed: {tests_failed}/3")
    
    if tests_failed == 0:
        print()
        print("🎉 All tests passed! The Plumbus is working perfectly!")
        print("   The dinglebop has been smoothed, the schleem repurposed,")
        print("   and the Shlami is ready to rub everything with fleeb juice!")
        print("=" * 70)
        sys.exit(0)
    else:
        print()
        print("❌ Some tests failed. The Plumbus needs adjustment.")
        print("=" * 70)
        sys.exit(1)
