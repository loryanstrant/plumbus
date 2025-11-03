"""
SSH Client module for Plumbus
Handles SSH connections and remote file operations
"""
import paramiko
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SSHClient:
    def __init__(self, host: str, port: int, username: str, 
                 password: Optional[str] = None, key_path: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self.client = None
    
    def connect(self):
        """Establish SSH connection"""
        if self.client:
            return self.client
        
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.key_path and os.path.exists(self.key_path):
                # Use SSH key authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=10
                )
            elif self.password:
                # Use password authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            else:
                raise ValueError("No authentication method provided")
            
            logger.info(f"Connected to {self.username}@{self.host}:{self.port}")
            return self.client
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}: {e}")
            raise
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            self.client = None
            logger.info(f"Disconnected from {self.host}")
    
    def test_connection(self) -> Dict:
        """Test SSH connection and return result"""
        try:
            self.connect()
            
            # Try to execute a simple command
            stdin, stdout, stderr = self.client.exec_command('uname -a')
            uname = stdout.read().decode().strip()
            
            self.disconnect()
            
            return {
                'success': True,
                'message': f'Connection successful',
                'system_info': uname
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'error': 'Failed to connect. Please check host, port, and credentials.'
            }
    
    def execute_command(self, command: str) -> Dict:
        """Execute a command on the remote host"""
        try:
            self.connect()
            stdin, stdout, stderr = self.client.exec_command(command)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                'success': exit_code == 0,
                'output': output,
                'error': error,
                'exit_code': exit_code
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_directory(self, path: str = '/') -> List[Dict]:
        """List files and directories at the given path"""
        try:
            self.connect()
            sftp = self.client.open_sftp()
            
            # Normalize path
            if not path:
                path = '/'
            
            try:
                files = []
                for item in sftp.listdir_attr(path):
                    file_info = {
                        'name': item.filename,
                        'size': item.st_size,
                        'modified': item.st_mtime,
                        'is_dir': self._is_directory(item.st_mode),
                        'permissions': oct(item.st_mode)[-3:]
                    }
                    files.append(file_info)
                
                # Sort: directories first, then files, alphabetically
                files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
                
                sftp.close()
                return files
            except IOError as e:
                logger.error(f"Failed to list directory {path}: {e}")
                sftp.close()
                raise
        except Exception as e:
            logger.error(f"Failed to list directory: {e}")
            raise
    
    def _is_directory(self, mode: int) -> bool:
        """Check if the file mode indicates a directory"""
        import stat
        return stat.S_ISDIR(mode)
    
    def get_file_info(self, path: str) -> Optional[Dict]:
        """Get information about a file or directory"""
        try:
            self.connect()
            sftp = self.client.open_sftp()
            
            stat_info = sftp.stat(path)
            
            info = {
                'size': stat_info.st_size,
                'modified': stat_info.st_mtime,
                'is_dir': self._is_directory(stat_info.st_mode),
                'permissions': oct(stat_info.st_mode)[-3:]
            }
            
            sftp.close()
            return info
        except Exception as e:
            logger.error(f"Failed to get file info for {path}: {e}")
            return None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
