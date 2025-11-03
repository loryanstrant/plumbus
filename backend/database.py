"""
Database module for PLUMBUS
Handles all database operations using SQLite

This is the dinglebop storage facility - where all the smoothed-out configurations live!
"""
import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 22,
                username TEXT NOT NULL,
                auth_method TEXT DEFAULT 'password',
                password TEXT,
                key_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                source_path TEXT NOT NULL,
                schedule TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            )
        ''')
        
        # Backups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                size_bytes INTEGER,
                file_count INTEGER,
                error_message TEXT,
                backup_path TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    # Client operations
    def add_client(self, name, host, port, username, auth_method='password', 
                   password=None, key_path=None):
        """Add a new client"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clients (name, host, port, username, auth_method, password, key_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, host, port, username, auth_method, password, key_path))
        client_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Added client: {name} (ID: {client_id})")
        return client_id
    
    def get_client(self, client_id):
        """Get a client by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_clients(self):
        """Get all clients"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_client(self, client_id, data):
        """Update a client"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        for key, value in data.items():
            if key not in ['id', 'created_at']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(client_id)
            
            query = f"UPDATE clients SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
        logger.info(f"Updated client ID: {client_id}")
    
    def delete_client(self, client_id):
        """Delete a client"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        conn.commit()
        conn.close()
        logger.info(f"Deleted client ID: {client_id}")
    
    # Job operations
    def add_job(self, client_id, name, source_path, schedule=None, enabled=True):
        """Add a new backup job"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO jobs (client_id, name, source_path, schedule, enabled)
            VALUES (?, ?, ?, ?, ?)
        ''', (client_id, name, source_path, schedule, 1 if enabled else 0))
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Added job: {name} (ID: {job_id})")
        return job_id
    
    def get_job(self, job_id):
        """Get a job by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT j.*, c.name as client_name, c.host, c.username
            FROM jobs j
            LEFT JOIN clients c ON j.client_id = c.id
            WHERE j.id = ?
        ''', (job_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_jobs(self):
        """Get all jobs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT j.*, c.name as client_name, c.host
            FROM jobs j
            LEFT JOIN clients c ON j.client_id = c.id
            ORDER BY j.name
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_job(self, job_id, data):
        """Update a job"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        for key, value in data.items():
            if key not in ['id', 'created_at', 'client_name', 'host']:
                if key == 'enabled' and isinstance(value, bool):
                    value = 1 if value else 0
                fields.append(f"{key} = ?")
                values.append(value)
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(job_id)
            
            query = f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
        logger.info(f"Updated job ID: {job_id}")
    
    def delete_job(self, job_id):
        """Delete a job"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
        conn.commit()
        conn.close()
        logger.info(f"Deleted job ID: {job_id}")
    
    def update_job_last_run(self, job_id):
        """Update the last run time for a job"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE jobs SET last_run = ? WHERE id = ?
        ''', (datetime.now().isoformat(), job_id))
        conn.commit()
        conn.close()
    
    # Backup operations
    def add_backup(self, job_id, status, start_time, backup_path=None):
        """Add a new backup record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO backups (job_id, status, start_time, backup_path)
            VALUES (?, ?, ?, ?)
        ''', (job_id, status, start_time, backup_path))
        backup_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return backup_id
    
    def update_backup(self, backup_id, status=None, end_time=None, size_bytes=None,
                     file_count=None, error_message=None):
        """Update a backup record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        
        if status:
            fields.append("status = ?")
            values.append(status)
        if end_time:
            fields.append("end_time = ?")
            values.append(end_time)
        if size_bytes is not None:
            fields.append("size_bytes = ?")
            values.append(size_bytes)
        if file_count is not None:
            fields.append("file_count = ?")
            values.append(file_count)
        if error_message:
            fields.append("error_message = ?")
            values.append(error_message)
        
        if fields:
            values.append(backup_id)
            query = f"UPDATE backups SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
    
    def get_job_history(self, job_id, limit=50):
        """Get backup history for a job"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM backups
            WHERE job_id = ?
            ORDER BY start_time DESC
            LIMIT ?
        ''', (job_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_all_backups(self, limit=100):
        """Get all backups"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.*, j.name as job_name, c.name as client_name
            FROM backups b
            LEFT JOIN jobs j ON b.job_id = j.id
            LEFT JOIN clients c ON j.client_id = c.id
            ORDER BY b.start_time DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_backup(self, backup_id):
        """Get a backup by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.*, j.name as job_name, j.client_id, j.source_path
            FROM backups b
            LEFT JOIN jobs j ON b.job_id = j.id
            WHERE b.id = ?
        ''', (backup_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
