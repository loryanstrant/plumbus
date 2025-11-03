"""
Backup Manager module for PLUMBUS
Handles backup job execution, scheduling, and restoration

This is where the Shlami rubs everything with fleeb juice (SSH + rsync).
The schleem from earlier batches is repurposed here for scheduled backups.
"""
import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.ssh_client import SSHClient

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, database, backup_dir):
        self.db = database
        self.backup_dir = backup_dir
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._load_scheduled_jobs()
    
    def _load_scheduled_jobs(self):
        """Load and schedule all enabled jobs from database
        
        The schleem from earlier batches gets repurposed here!
        """
        jobs = self.db.get_all_jobs()
        for job in jobs:
            if job['enabled'] and job['schedule']:
                try:
                    self.schedule_job(job['id'])
                    logger.info(f"Scheduled job {job['id']}: {job['name']}")
                except Exception as e:
                    logger.error(f"Failed to schedule job {job['id']}: {e}")
    
    def schedule_job(self, job_id):
        """Schedule a backup job using cron expression"""
        job = self.db.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        if not job['schedule']:
            logger.warning(f"Job {job_id} has no schedule")
            return
        
        # Parse cron expression (format: "minute hour day month day_of_week")
        # Example: "0 2 * * *" = daily at 2am
        try:
            parts = job['schedule'].split()
            if len(parts) != 5:
                logger.error(f"Invalid cron expression for job {job_id}: {job['schedule']}")
                return
            
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4]
            )
            
            self.scheduler.add_job(
                func=self._run_scheduled_backup,
                trigger=trigger,
                args=[job_id],
                id=f"job_{job_id}",
                replace_existing=True
            )
            logger.info(f"Scheduled job {job_id} with cron: {job['schedule']}")
        except Exception as e:
            logger.error(f"Failed to schedule job {job_id}: {e}")
    
    def unschedule_job(self, job_id):
        """Remove a job from the scheduler"""
        try:
            self.scheduler.remove_job(f"job_{job_id}")
            logger.info(f"Unscheduled job {job_id}")
        except Exception as e:
            logger.debug(f"Job {job_id} was not scheduled: {e}")
    
    def _run_scheduled_backup(self, job_id):
        """Internal method called by scheduler"""
        logger.info(f"Running scheduled backup for job {job_id}")
        self.run_backup_job(job_id)
    
    def run_backup_job(self, job_id):
        """Execute a backup job
        
        Time for the Shlami to show up and rub everything with fleeb juice!
        """
        job = self.db.get_job(job_id)
        if not job:
            return {'success': False, 'error': 'Job not found'}
        
        client = self.db.get_client(job['client_id'])
        if not client:
            return {'success': False, 'error': 'Client not found'}
        
        start_time = datetime.now()
        backup_name = f"{job['name']}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.backup_dir, str(job['client_id']), backup_name)
        
        # Create backup directory
        os.makedirs(backup_path, exist_ok=True)
        
        # Create backup record
        backup_id = self.db.add_backup(
            job_id=job_id,
            status='running',
            start_time=start_time.isoformat(),
            backup_path=backup_path
        )
        
        try:
            logger.info(f"Starting backup {backup_id} for job {job_id}")
            
            # Build rsync command
            rsync_cmd = self._build_rsync_command(client, job['source_path'], backup_path)
            
            # Execute rsync (don't log command to avoid exposing passwords)
            logger.info(f"Executing backup command for job {job_id} (credentials redacted)")
            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            # Calculate backup size and file count
            size_bytes = self._calculate_directory_size(backup_path)
            file_count = self._count_files(backup_path)
            
            if result.returncode == 0:
                # Backup successful - The plumbus is now ready!
                self.db.update_backup(
                    backup_id=backup_id,
                    status='completed',
                    end_time=datetime.now().isoformat(),
                    size_bytes=size_bytes,
                    file_count=file_count
                )
                self.db.update_job_last_run(job_id)
                
                logger.info(f"Backup {backup_id} completed successfully")
                return {
                    'success': True,
                    'backup_id': backup_id,
                    'size_bytes': size_bytes,
                    'file_count': file_count
                }
            else:
                # Backup failed
                error_msg = result.stderr or result.stdout
                self.db.update_backup(
                    backup_id=backup_id,
                    status='failed',
                    end_time=datetime.now().isoformat(),
                    error_message=error_msg
                )
                
                logger.error(f"Backup {backup_id} failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        
        except subprocess.TimeoutExpired:
            error_msg = "Backup timed out after 1 hour"
            self.db.update_backup(
                backup_id=backup_id,
                status='failed',
                end_time=datetime.now().isoformat(),
                error_message=error_msg
            )
            logger.error(f"Backup {backup_id} timed out")
            return {'success': False, 'error': error_msg}
        
        except Exception as e:
            error_msg = str(e)
            self.db.update_backup(
                backup_id=backup_id,
                status='failed',
                end_time=datetime.now().isoformat(),
                error_message=error_msg
            )
            logger.error(f"Backup {backup_id} failed with exception: {e}")
            return {'success': False, 'error': error_msg}
    
    def _build_rsync_command(self, client, source_path, dest_path):
        """Build rsync command for backup"""
        # Build SSH connection string
        ssh_cmd = f"ssh -p {client['port']} -o StrictHostKeyChecking=no"
        
        if client.get('key_path'):
            ssh_cmd += f" -i {client['key_path']}"
        
        # Build rsync command
        rsync_cmd = [
            'rsync',
            '-avz',  # archive, verbose, compress
            '--delete',  # delete files that don't exist on source
            '-e', ssh_cmd
        ]
        
        # Add sudo support on remote side if enabled
        if client.get('use_sudo'):
            rsync_cmd.extend(['--rsync-path', 'sudo rsync'])
            logger.info("Using sudo rsync on remote side")
        
        rsync_cmd.extend([
            f"{client['username']}@{client['host']}:{source_path}",
            dest_path
        ])
        
        # Add password authentication using sshpass if needed
        if client.get('password') and not client.get('key_path'):
            # Use sshpass for password authentication
            rsync_cmd = ['sshpass', '-p', client['password']] + rsync_cmd
            logger.info("Using password authentication with sshpass")
        
        return rsync_cmd
    
    def _calculate_directory_size(self, path):
        """Calculate total size of directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.error(f"Error calculating directory size: {e}")
        return total_size
    
    def _count_files(self, path):
        """Count number of files in directory"""
        count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                count += len(filenames)
        except Exception as e:
            logger.error(f"Error counting files: {e}")
        return count
    
    def restore_backup(self, backup_id, restore_path=None):
        """Restore a backup to the client"""
        backup = self.db.get_backup(backup_id)
        if not backup:
            return {'success': False, 'error': 'Backup not found'}
        
        job = self.db.get_job(backup['job_id'])
        if not job:
            return {'success': False, 'error': 'Job not found'}
        
        client = self.db.get_client(job['client_id'])
        if not client:
            return {'success': False, 'error': 'Client not found'}
        
        # Use original source path if restore_path not specified
        if not restore_path:
            restore_path = backup['source_path']
        
        # Validate restore_path to prevent path traversal attacks
        if not restore_path.startswith('/'):
            return {'success': False, 'error': 'Restore path must be absolute'}
        
        # Basic validation - no dangerous characters
        dangerous_chars = [';', '&', '|', '`', '$', '\n', '\r']
        if any(char in restore_path for char in dangerous_chars):
            return {'success': False, 'error': 'Invalid restore path'}
        
        try:
            logger.info(f"Starting restore of backup {backup_id} to {restore_path}")
            
            # Build rsync command for restore (reverse direction)
            ssh_cmd = f"ssh -p {client['port']} -o StrictHostKeyChecking=no"
            if client.get('key_path'):
                ssh_cmd += f" -i {client['key_path']}"
            
            rsync_cmd = [
                'rsync',
                '-avz',
                '-e', ssh_cmd
            ]
            
            # Add sudo support on remote side if enabled
            if client.get('use_sudo'):
                rsync_cmd.extend(['--rsync-path', 'sudo rsync'])
            
            rsync_cmd.extend([
                backup['backup_path'] + '/',
                f"{client['username']}@{client['host']}:{restore_path}"
            ])
            
            # Add password authentication using sshpass if needed
            if client.get('password') and not client.get('key_path'):
                rsync_cmd = ['sshpass', '-p', client['password']] + rsync_cmd
            
            logger.info(f"Executing restore command")
            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                logger.info(f"Restore of backup {backup_id} completed successfully")
                return {'success': True, 'message': 'Restore completed successfully'}
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Restore of backup {backup_id} failed: {error_msg}")
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            logger.error(f"Restore failed with exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_statistics(self):
        """Get backup statistics"""
        try:
            clients = self.db.get_all_clients()
            jobs = self.db.get_all_jobs()
            backups = self.db.get_all_backups(limit=1000)
            
            total_size = sum(b.get('size_bytes', 0) or 0 for b in backups if b['status'] == 'completed')
            successful_backups = len([b for b in backups if b['status'] == 'completed'])
            failed_backups = len([b for b in backups if b['status'] == 'failed'])
            
            return {
                'total_clients': len(clients),
                'total_jobs': len(jobs),
                'enabled_jobs': len([j for j in jobs if j['enabled']]),
                'total_backups': len(backups),
                'successful_backups': successful_backups,
                'failed_backups': failed_backups,
                'total_size_bytes': total_size,
                'total_size_gb': round(total_size / (1024**3), 2)
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
