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

def test_sudo_support():
    """Test sudo support in backup operations"""
    print("🧪 Testing sudo support...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    with tempfile.TemporaryDirectory() as backup_dir:
        try:
            # Create database
            db = Database(db_path)
            print("   ✓ Database created")
            
            # Add a client without sudo
            client_id_no_sudo = db.add_client(
                name="Test Client No Sudo",
                host="192.168.1.100",
                port=22,
                username="testuser",
                password="testpass",
                use_sudo=False
            )
            
            # Add a client with sudo
            client_id_with_sudo = db.add_client(
                name="Test Client With Sudo",
                host="192.168.1.101",
                port=22,
                username="testuser",
                password="testpass",
                use_sudo=True
            )
            print("   ✓ Clients added with and without sudo")
            
            # Get clients and verify use_sudo field
            client_no_sudo = db.get_client(client_id_no_sudo)
            client_with_sudo = db.get_client(client_id_with_sudo)
            
            assert client_no_sudo['use_sudo'] == 0, "Client without sudo should have use_sudo=0"
            assert client_with_sudo['use_sudo'] == 1, "Client with sudo should have use_sudo=1"
            print("   ✓ use_sudo field correctly stored")
            
            # Test BackupManager with sudo
            from backend.backup_manager import BackupManager
            backup_manager = BackupManager(db, backup_dir)
            
            # Test _build_rsync_command with sudo enabled
            rsync_cmd = backup_manager._build_rsync_command(
                client_with_sudo,
                "/etc/nut",
                "/tmp/backup"
            )
            
            # Check that --rsync-path sudo rsync is in the command
            assert '--rsync-path' in rsync_cmd, "rsync command should contain --rsync-path"
            rsync_path_idx = rsync_cmd.index('--rsync-path')
            assert rsync_cmd[rsync_path_idx + 1] == 'sudo rsync', "rsync-path should be 'sudo rsync'"
            print("   ✓ rsync command includes sudo when use_sudo is enabled")
            
            # Test _build_rsync_command without sudo
            rsync_cmd_no_sudo = backup_manager._build_rsync_command(
                client_no_sudo,
                "/home/testuser",
                "/tmp/backup"
            )
            
            # Check that --rsync-path is NOT in the command
            assert '--rsync-path' not in rsync_cmd_no_sudo, "rsync command should not contain --rsync-path when sudo is disabled"
            print("   ✓ rsync command does not include sudo when use_sudo is disabled")
            
            # Test update client with sudo
            db.update_client(client_id_no_sudo, {'use_sudo': True})
            updated_client = db.get_client(client_id_no_sudo)
            assert updated_client['use_sudo'] == 1, "Client should have use_sudo=1 after update"
            print("   ✓ Client use_sudo field can be updated")
            
            print("✅ Sudo support tests passed!")
            return True
            
        except Exception as e:
            print(f"   ❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

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
    
    if test_sudo_support():
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    print("=" * 70)
    print(f"Tests passed: {tests_passed}/4")
    print(f"Tests failed: {tests_failed}/4")
    
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
