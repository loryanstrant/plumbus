# PLUMBUS
## Persistent Linux Unified Multi-device Backup & Update System

![PLUMBUS](https://img.shields.io/badge/PLUMBUS-Backup%20System-blue)
![Docker](https://img.shields.io/badge/docker-multi--arch-blue)
![License](https://img.shields.io/badge/license-MIT-green)

*Everyone has a Plumbus in their home... now every Linux cluster can have one too!*

Nobody really knows how Plumbus works, but it keeps your data safe through a carefully refined process involving schleem, fleeb juice, and just the right amount of quantum entanglement. The dinglebop is then smoothed out with a bunch of schleem (which is repurposed for later backups).

## What is PLUMBUS?

PLUMBUS is a centralized backup solution for Raspberry Pi, Linux servers, and other devices across different VLANs. It runs as a Docker container and provides a beautiful web interface for managing your backups.

### Features

- 🚀 **Multi-Architecture Support**: Works on ARM and x86 systems (32-bit and 64-bit)
- 🌐 **Web Interface**: Beautiful UI for managing clients, jobs, and backups
- 🔄 **Automated Backups**: Schedule backups using cron expressions
- 📁 **File Browser**: Browse remote filesystems to select backup paths
- 🔐 **SSH/Rsync Based**: Agent-less backups using standard SSH
- 🏠 **VLAN-Friendly**: Works across different network segments
- 📊 **Backup Statistics**: Track backup sizes, success rates, and history
- ↻ **Restore Capability**: Easy restoration of backed-up files

### How PLUMBUS is Made

Regular old Plumbus manufacturing:
1. First they take the dinglebop and smooth it out with a bunch of schleem
2. The schleem is then repurposed for later batches
3. They take the dinglebop and push it through the grumbo
4. A Shlami shows up and rubs it with fleeb juice

PLUMBUS Backup System manufacturing:
1. First, you deploy the Docker container (the dinglebop)
2. Configure your backup clients (smoothing with schleem)
3. Set up backup jobs (pushing through the grumbo)
4. Watch as backups run automatically (the Shlami does its job)
5. Your data is safe! (Everyone has a Plumbus!)

## Quick Start

### Pull from GitHub Container Registry

```bash
# For multi-arch (automatically selects the right architecture)
docker pull ghcr.io/loryanstrant/plumbus:latest

# Or use docker-compose
docker-compose up -d
```

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/loryanstrant/plumbus.git
cd plumbus

# Start the container
docker-compose up -d

# Access the web interface
open http://localhost:5000
```

### Manual Docker Run

```bash
docker run -d \
  -p 5000:5000 \
  -v plumbus-data:/data \
  --name plumbus-backup \
  ghcr.io/loryanstrant/plumbus:latest
```

## Configuration

### Adding a Client

1. Open the web interface at `http://your-server:5000`
2. Click "Add Client" 
3. Enter your Raspberry Pi or Linux server details:
   - Name (e.g., "Raspberry Pi Zero 2 W")
   - Host (IP address or hostname)
   - SSH credentials (password or key-based authentication)
4. Test the connection to ensure it works

### Creating a Backup Job

1. Go to the "Backup Jobs" tab
2. Click "Add Job"
3. Select your client
4. Use the file browser to select what to backup
5. Set a schedule (or leave empty for manual backups)
6. Enable the job

### Scheduling Format

Use cron expressions for scheduling:
- `0 2 * * *` - Daily at 2 AM
- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 */6 * * *` - Every 6 hours
- `*/30 * * * *` - Every 30 minutes

## Architecture Support

PLUMBUS supports all major architectures:
- `linux/amd64` (x86 64-bit)
- `linux/arm64` (ARM 64-bit, like Raspberry Pi 3/4/Zero 2 W)
- `linux/arm/v7` (ARM 32-bit, like older Raspberry Pi)
- `linux/386` (x86 32-bit)

The Docker image automatically detects and uses the correct architecture.

## Requirements

### Backup Server (where PLUMBUS runs)
- Docker and Docker Compose
- Persistent storage for backups
- Network access to backup clients

### Backup Clients (what you're backing up)
- SSH server running
- rsync installed
- Network connectivity to backup server

## API Documentation

PLUMBUS provides a REST API for automation:

- `GET /api/clients` - List all clients
- `POST /api/clients` - Add a new client
- `GET /api/jobs` - List all backup jobs
- `POST /api/jobs` - Create a backup job
- `POST /api/jobs/{id}/run` - Run a job immediately
- `GET /api/backups` - List backup history
- `POST /api/backups/{id}/restore` - Restore a backup

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
python app.py

# Build Docker image locally
docker build -t plumbus .
```

## Troubleshooting

**Q: Why doesn't my backup work?**
A: Just like a regular Plumbus, sometimes you need to smooth out the dinglebop. Check:
- SSH connectivity to your client
- Sufficient disk space on the backup server
- Correct source path on the client

**Q: Can I backup across VLANs?**
A: Yes! As long as the backup server can reach your clients via SSH (port 22 by default).

**Q: Does this support Windows?**
A: PLUMBUS is designed for Linux systems. Windows support would require significant schleem repurposing.

## Contributing

Everyone knows about Plumbus, but contributions are always welcome! 
Please submit pull requests or open issues on GitHub.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Inspired by the mysterious Plumbus from Rick and Morty
- Built with Flask, Paramiko, and rsync
- Powered by fleeb juice and quantum entanglement
