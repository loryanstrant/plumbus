"""
PLUMBUS - Persistent Linux Unified Multi-device Backup & Update System
Main application file

Everyone has a Plumbus in their home... now every Linux cluster can have one too!

How PLUMBUS is made:
1. First, take the dinglebop (Docker container) and smooth it out with schleem (configuration)
2. The schleem is repurposed for later batches (scheduled backups)  
3. Push it through the grumbo (backup execution engine)
4. A Shlami shows up and rubs it with fleeb juice (SSH + rsync)
5. Your data is safe! (Everyone has a PLUMBUS!)
"""
import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from backend.ssh_client import SSHClient
from backend.backup_manager import BackupManager
from backend.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Configuration
DATA_DIR = os.environ.get('DATA_DIR', '/data')
DB_PATH = os.path.join(DATA_DIR, 'db', 'plumbus.db')
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')

# Ensure directories exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Initialize database and backup manager
db = Database(DB_PATH)
backup_manager = BackupManager(db, BACKUP_DIR)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/clients', methods=['GET', 'POST'])
def clients():
    """Manage backup clients"""
    if request.method == 'POST':
        data = request.json
        try:
            client_id = db.add_client(
                name=data['name'],
                host=data['host'],
                port=data.get('port', 22),
                username=data['username'],
                auth_method=data.get('auth_method', 'password'),
                password=data.get('password'),
                key_path=data.get('key_path'),
                use_sudo=data.get('use_sudo', False)
            )
            return jsonify({'success': True, 'client_id': client_id})
        except Exception as e:
            logger.error(f"Error adding client: {e}")
            return jsonify({'success': False, 'error': 'Failed to add client'}), 400
    else:
        clients = db.get_all_clients()
        return jsonify(clients)

@app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
def client_detail(client_id):
    """Get, update or delete a specific client"""
    if request.method == 'DELETE':
        db.delete_client(client_id)
        return jsonify({'success': True})
    elif request.method == 'PUT':
        data = request.json
        db.update_client(client_id, data)
        return jsonify({'success': True})
    else:
        client = db.get_client(client_id)
        if client:
            return jsonify(client)
        return jsonify({'error': 'Client not found'}), 404

@app.route('/api/clients/<int:client_id>/test', methods=['POST'])
def test_client_connection(client_id):
    """Test SSH connection to a client"""
    try:
        client = db.get_client(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        ssh_client = SSHClient(
            host=client['host'],
            port=client['port'],
            username=client['username'],
            password=client.get('password'),
            key_path=client.get('key_path')
        )
        
        # Check sudo access if use_sudo is enabled
        check_sudo = bool(client.get('use_sudo', False))
        result = ssh_client.test_connection(check_sudo=check_sudo)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({'success': False, 'error': 'Connection test failed'}), 400

@app.route('/api/clients/<int:client_id>/browse', methods=['POST'])
def browse_client_files(client_id):
    """Browse files on a client"""
    try:
        client = db.get_client(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        data = request.json
        path = data.get('path', '/')
        
        ssh_client = SSHClient(
            host=client['host'],
            port=client['port'],
            username=client['username'],
            password=client.get('password'),
            key_path=client.get('key_path')
        )
        
        files = ssh_client.list_directory(path)
        return jsonify({'success': True, 'path': path, 'files': files})
    except Exception as e:
        logger.error(f"Error browsing files: {e}")
        return jsonify({'success': False, 'error': 'Failed to browse files'}), 400

@app.route('/api/jobs', methods=['GET', 'POST'])
def jobs():
    """Manage backup jobs"""
    if request.method == 'POST':
        data = request.json
        try:
            job_id = db.add_job(
                client_id=data['client_id'],
                name=data['name'],
                source_path=data['source_path'],
                schedule=data.get('schedule'),
                enabled=data.get('enabled', True)
            )
            
            # Schedule the job if enabled
            if data.get('enabled', True) and data.get('schedule'):
                backup_manager.schedule_job(job_id)
            
            return jsonify({'success': True, 'job_id': job_id})
        except Exception as e:
            logger.error(f"Error adding job: {e}")
            return jsonify({'success': False, 'error': 'Failed to add job'}), 400
    else:
        jobs = db.get_all_jobs()
        return jsonify(jobs)

@app.route('/api/jobs/<int:job_id>', methods=['GET', 'PUT', 'DELETE'])
def job_detail(job_id):
    """Get, update or delete a specific job"""
    if request.method == 'DELETE':
        backup_manager.unschedule_job(job_id)
        db.delete_job(job_id)
        return jsonify({'success': True})
    elif request.method == 'PUT':
        data = request.json
        db.update_job(job_id, data)
        
        # Reschedule if schedule changed
        if 'schedule' in data or 'enabled' in data:
            backup_manager.unschedule_job(job_id)
            job = db.get_job(job_id)
            if job and job['enabled'] and job['schedule']:
                backup_manager.schedule_job(job_id)
        
        return jsonify({'success': True})
    else:
        job = db.get_job(job_id)
        if job:
            return jsonify(job)
        return jsonify({'error': 'Job not found'}), 404

@app.route('/api/jobs/<int:job_id>/run', methods=['POST'])
def run_job(job_id):
    """Run a backup job immediately"""
    try:
        result = backup_manager.run_backup_job(job_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running job: {e}")
        return jsonify({'success': False, 'error': 'Failed to run backup job'}), 400

@app.route('/api/jobs/<int:job_id>/history', methods=['GET'])
def job_history(job_id):
    """Get backup history for a job"""
    history = db.get_job_history(job_id)
    return jsonify(history)

@app.route('/api/backups', methods=['GET'])
def list_backups():
    """List all backups"""
    backups = db.get_all_backups()
    return jsonify(backups)

@app.route('/api/backups/<int:backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    """Restore a backup"""
    try:
        data = request.json
        restore_path = data.get('restore_path')
        result = backup_manager.restore_backup(backup_id, restore_path)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return jsonify({'success': False, 'error': 'Failed to restore backup'}), 400

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get backup statistics"""
    stats = backup_manager.get_statistics()
    return jsonify(stats)

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🛸 Starting PLUMBUS Backup Server")
    logger.info("   Persistent Linux Unified Multi-device Backup & Update System")
    logger.info("=" * 70)
    logger.info("Everyone has a Plumbus... now your cluster does too!")
    logger.info(f"📁 Data directory: {DATA_DIR}")
    logger.info(f"💾 Database: {DB_PATH}")
    logger.info(f"🗄️  Backup directory: {BACKUP_DIR}")
    logger.info("🔧 Smoothing out the dinglebop...")
    logger.info("✨ Ready to repurpose some schleem!")
    logger.info("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
