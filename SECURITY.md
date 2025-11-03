# Security Summary for PLUMBUS

## CodeQL Analysis Results

This document explains the remaining CodeQL alerts and their mitigation strategies.

### Resolved Alerts ✅

The following security issues have been fixed:

1. **Clear-text password logging** - Passwords are now redacted from logs
2. **Stack trace exposure in error responses** - Generic error messages are returned to users
3. **Multiple SQL injection vectors** - Implemented field whitelisting for UPDATE queries

### Remaining Alerts and Mitigations

#### 1. Command Line Injection (py/command-line-injection)
**Location**: `backend/backup_manager.py` line 294

**Issue**: The restore functionality uses user-provided `restore_path` in rsync command.

**Mitigation**:
- Restore path is validated to be an absolute path starting with `/`
- Dangerous characters (`;`, `&`, `|`, backticks, `$`, newlines) are blocked
- The path is used in subprocess.run() with shell=False (array form)
- This is necessary functionality for restore operations

**Risk Level**: Low - Input validation prevents command injection

#### 2. Paramiko Missing Host Key Validation (py/paramiko-missing-host-key-validation)
**Location**: `backend/ssh_client.py` line 28

**Issue**: Uses `AutoAddPolicy()` which automatically accepts SSH host keys.

**Mitigation**:
- This is intentional for ease of use in home/lab environments
- Documented in README security section
- Users can manually verify host keys before adding clients
- For production: recommend using SSH key-based auth with pre-verified host keys

**Risk Level**: Medium - Acceptable for target use case (home labs, internal networks)

#### 3. SQL Injection (py/sql-injection)
**Location**: `backend/database.py` lines 137, 218

**Issue**: Dynamic SQL query construction with user input.

**Actual Risk**: FALSE POSITIVE
- Field names come from a whitelist, not user input
- All values use parameterized queries (`?` placeholders)
- The string interpolation is only for field names from the whitelist
- User-provided values never directly enter the SQL string

**Example**:
```python
allowed_fields = ['name', 'host', 'port', ...]  # Whitelist
for key, value in data.items():
    if key in allowed_fields:  # Only whitelisted fields
        fields.append(f"{key} = ?")  # Safe: key is from whitelist
        values.append(value)  # Safe: goes through parameterization
query = f"UPDATE ... SET {', '.join(fields)} WHERE id = ?"
cursor.execute(query, values)  # Parameterized execution
```

**Risk Level**: None - False positive

## Security Best Practices for Deployment

### Recommended Configuration

1. **Use SSH Key Authentication**
   ```python
   # Preferred over password authentication
   key_path = "/path/to/private/key"
   ```

2. **Secure the Database**
   ```bash
   chmod 600 /data/db/plumbus.db
   chown app-user:app-user /data/db/plumbus.db
   ```

3. **Network Security**
   - Deploy behind a reverse proxy with HTTPS
   - Use firewall rules to restrict access
   - Consider VPN for remote access

4. **Docker Security**
   ```yaml
   services:
     plumbus:
       read_only: true
       security_opt:
         - no-new-privileges:true
       cap_drop:
         - ALL
   ```

5. **Regular Updates**
   ```bash
   docker pull ghcr.io/loryanstrant/plumbus:latest
   docker-compose up -d
   ```

### Known Limitations

1. **Password Storage**: Passwords stored in SQLite database
   - Mitigation: Use SSH keys instead
   - Mitigation: Secure database file with filesystem permissions
   - Future: Consider adding encryption at rest

2. **No User Authentication**: Web interface has no built-in auth
   - Mitigation: Deploy behind reverse proxy with authentication
   - Mitigation: Use network-level access controls
   - Future: Consider adding OAuth/OIDC support

3. **Host Key Management**: Automatic acceptance of SSH host keys
   - Mitigation: Manually verify hosts before first connection
   - Mitigation: Use SSH keys for added security
   - Future: Consider adding host key pinning

## Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email the maintainer directly with details
3. Allow reasonable time for a fix before disclosure

## Security Changelog

- **v1.0.0** (2025-11-03):
  - Fixed clear-text password logging
  - Fixed stack trace exposure
  - Added input validation for restore paths
  - Implemented SQL query field whitelisting
  - Added sshpass for password authentication
  - Documented security best practices

---

Remember: Everyone has a Plumbus, but not everyone secures it properly! 🛸🔒
