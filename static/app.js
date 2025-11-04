// Plumbus Backup Server - Client-side JavaScript

// Constants
const DEFAULT_SCHEDULE_HOUR = 2;  // 2 AM
const DEFAULT_SCHEDULE_MINUTE = 0;  // :00

// Global state
let currentClient = null;
let currentPath = '/';
let currentEditMode = null; // 'add' or 'edit' for file browser context
let allJobs = [];
let allBackups = [];
let allClients = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    loadVersion();
    loadStats();
    loadClients();
    loadJobs();
    loadBackups();
    
    // Refresh stats every 30 seconds
    setInterval(loadStats, 30000);
});

// Tab Management
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// API Functions
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Request failed');
        }
        
        return result;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Version
async function loadVersion() {
    try {
        const result = await apiCall('/api/version');
        document.getElementById('version-display').textContent = `Version: ${result.version}`;
    } catch (error) {
        console.error('Failed to load version:', error);
        document.getElementById('version-display').textContent = 'Version: Unknown';
    }
}

// Statistics
async function loadStats() {
    try {
        const stats = await apiCall('/api/stats');
        document.getElementById('stat-clients').textContent = stats.total_clients || 0;
        document.getElementById('stat-jobs').textContent = stats.total_jobs || 0;
        document.getElementById('stat-backups').textContent = stats.successful_backups || 0;
        document.getElementById('stat-size').textContent = (stats.total_size_gb || 0) + ' GB';
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Clients Management
async function loadClients() {
    try {
        const clients = await apiCall('/api/clients');
        allClients = clients;
        const container = document.getElementById('clients-list');
        
        if (clients.length === 0) {
            container.innerHTML = '<p class="empty-message">No clients configured yet. First, take the dinglebop and smooth it out... or just click "Add Client" above! 📦</p>';
            return;
        }
        
        container.innerHTML = clients.map(client => `
            <div class="list-item">
                <div class="item-info">
                    <div class="item-title">${escapeHtml(client.name)}</div>
                    <div class="item-meta">
                        ${escapeHtml(client.username)}@${escapeHtml(client.host)}:${client.port}
                        ${client.use_sudo ? ' | <strong>Using sudo</strong>' : ''}
                    </div>
                </div>
                <div class="item-actions">
                    <button class="btn btn-secondary btn-sm" onclick="testClient(${client.id})">Test</button>
                    <button class="btn btn-secondary btn-sm" onclick="showEditClientModal(${client.id})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteClient(${client.id})">Delete</button>
                </div>
            </div>
        `).join('');
        
        // Update client filter dropdowns
        updateClientFilters();
    } catch (error) {
        console.error('Failed to load clients:', error);
        showMessage('Failed to load clients', 'error');
    }
}

function showAddClientModal() {
    document.getElementById('add-client-modal').style.display = 'block';
}

async function addClient(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        name: formData.get('name'),
        host: formData.get('host'),
        port: parseInt(formData.get('port')),
        username: formData.get('username'),
        auth_method: formData.get('auth_method'),
        use_sudo: formData.get('use_sudo') === 'on'
    };
    
    if (data.auth_method === 'password') {
        data.password = formData.get('password');
    } else {
        data.key_path = formData.get('key_path');
    }
    
    try {
        await apiCall('/api/clients', 'POST', data);
        closeModal('add-client-modal');
        form.reset();
        loadClients();
        loadStats();
        showMessage('Client added successfully! The dinglebop has been smoothed! 🎉', 'success');
    } catch (error) {
        showMessage('Failed to add client: ' + error.message, 'error');
    }
}

async function showEditClientModal(clientId) {
    try {
        const client = await apiCall(`/api/clients/${clientId}`);
        
        document.getElementById('edit-client-id').value = client.id;
        document.getElementById('edit-client-name').value = client.name;
        document.getElementById('edit-client-host').value = client.host;
        document.getElementById('edit-client-port').value = client.port;
        document.getElementById('edit-client-username').value = client.username;
        document.getElementById('edit-client-auth-method').value = client.auth_method;
        document.getElementById('edit-client-use-sudo').checked = client.use_sudo === 1;
        
        if (client.auth_method === 'password') {
            document.getElementById('edit-password-field').style.display = 'block';
            document.getElementById('edit-key-field').style.display = 'none';
            document.getElementById('edit-client-password').value = '';
        } else {
            document.getElementById('edit-password-field').style.display = 'none';
            document.getElementById('edit-key-field').style.display = 'block';
            document.getElementById('edit-client-key-path').value = client.key_path || '';
        }
        
        document.getElementById('edit-client-modal').style.display = 'block';
    } catch (error) {
        showMessage('Failed to load client: ' + error.message, 'error');
    }
}

async function updateClient(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const clientId = formData.get('client_id');
    
    const data = {
        name: formData.get('name'),
        host: formData.get('host'),
        port: parseInt(formData.get('port')),
        username: formData.get('username'),
        auth_method: formData.get('auth_method'),
        use_sudo: formData.get('use_sudo') === 'on'
    };
    
    if (data.auth_method === 'password') {
        const password = formData.get('password');
        if (password) {
            data.password = password;
        }
    } else {
        data.key_path = formData.get('key_path');
    }
    
    try {
        await apiCall(`/api/clients/${clientId}`, 'PUT', data);
        closeModal('edit-client-modal');
        loadClients();
        loadStats();
        showMessage('Client updated successfully! 🎉', 'success');
    } catch (error) {
        showMessage('Failed to update client: ' + error.message, 'error');
    }
}

async function testClient(clientId) {
    try {
        const result = await apiCall(`/api/clients/${clientId}/test`, 'POST');
        if (result.success) {
            showMessage('Connection successful! The fleeb juice is flowing properly! 🎯 ' + result.system_info, 'success');
        } else {
            showMessage('Connection failed: ' + result.error, 'error');
        }
    } catch (error) {
        showMessage('Connection test failed: ' + error.message, 'error');
    }
}

async function deleteClient(clientId) {
    if (!confirm('Are you sure you want to delete this client?')) {
        return;
    }
    
    try {
        await apiCall(`/api/clients/${clientId}`, 'DELETE');
        loadClients();
        loadStats();
        showMessage('Client deleted successfully', 'success');
    } catch (error) {
        showMessage('Failed to delete client: ' + error.message, 'error');
    }
}

function toggleAuthFields(select) {
    const passwordField = document.getElementById('password-field');
    const keyField = document.getElementById('key-field');
    
    if (select.value === 'password') {
        passwordField.style.display = 'block';
        keyField.style.display = 'none';
    } else {
        passwordField.style.display = 'none';
        keyField.style.display = 'block';
    }
}

function toggleEditAuthFields(select) {
    const passwordField = document.getElementById('edit-password-field');
    const keyField = document.getElementById('edit-key-field');
    
    if (select.value === 'password') {
        passwordField.style.display = 'block';
        keyField.style.display = 'none';
    } else {
        passwordField.style.display = 'none';
        keyField.style.display = 'block';
    }
}

function updateClientFilters() {
    const jobFilter = document.getElementById('job-client-filter');
    const backupFilter = document.getElementById('backup-client-filter');
    
    const options = '<option value="">All Clients</option>' + 
        allClients.map(client => `<option value="${client.id}">${escapeHtml(client.name)}</option>`).join('');
    
    jobFilter.innerHTML = options;
    backupFilter.innerHTML = options;
}

// Jobs Management
async function loadJobs() {
    try {
        const jobs = await apiCall('/api/jobs');
        allJobs = jobs;
        displayJobs(jobs);
    } catch (error) {
        console.error('Failed to load jobs:', error);
        showMessage('Failed to load jobs', 'error');
    }
}

function displayJobs(jobs) {
    const container = document.getElementById('jobs-list');
    
    if (jobs.length === 0) {
        container.innerHTML = '<p class="empty-message">No backup jobs configured. The schleem is ready to be repurposed for later batches! Add a job to get started. 🔄</p>';
        return;
    }
    
    container.innerHTML = jobs.map(job => {
        const statusClass = job.enabled ? 'status-enabled' : 'status-disabled';
        const statusText = job.enabled ? 'Enabled' : 'Disabled';
        const lastRun = job.last_run ? new Date(job.last_run).toLocaleString() : 'Never';
        
        return `
            <div class="list-item" data-client-id="${job.client_id}">
                <div class="item-info">
                    <div class="item-title">${escapeHtml(job.name)}</div>
                    <div class="item-meta">
                        Client: ${escapeHtml(job.client_name)} | Path: ${escapeHtml(job.source_path)}<br>
                        Schedule: ${escapeHtml(job.schedule || 'Manual only')} | Last run: ${lastRun}
                    </div>
                </div>
                <div class="item-actions">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                    <button class="btn btn-success btn-sm" onclick="runJob(${job.id})">▶ Run Now</button>
                    <button class="btn btn-secondary btn-sm" onclick="showEditJobModal(${job.id})">Edit</button>
                    <button class="btn btn-secondary btn-sm" onclick="showJobHistory(${job.id})">History</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteJob(${job.id})">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

function filterJobs() {
    const clientId = document.getElementById('job-client-filter').value;
    if (clientId) {
        const filtered = allJobs.filter(job => job.client_id == clientId);
        displayJobs(filtered);
    } else {
        displayJobs(allJobs);
    }
}

async function showAddJobModal() {
    // Load clients into dropdown
    try {
        const clients = await apiCall('/api/clients');
        const select = document.getElementById('job-client-select');
        
        if (clients.length === 0) {
            showMessage('Please add a client first', 'error');
            return;
        }
        
        select.innerHTML = '<option value="">Select a client...</option>' +
            clients.map(client => `<option value="${client.id}">${escapeHtml(client.name)}</option>`).join('');
        
        document.getElementById('add-job-modal').style.display = 'block';
    } catch (error) {
        showMessage('Failed to load clients', 'error');
    }
}

async function addJob(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    // Build schedule from UI
    const schedule = buildScheduleFromUI('add');
    
    const data = {
        name: formData.get('name'),
        client_id: parseInt(formData.get('client_id')),
        source_path: formData.get('source_path'),
        schedule: schedule,
        enabled: formData.get('enabled') === 'on'
    };
    
    try {
        await apiCall('/api/jobs', 'POST', data);
        closeModal('add-job-modal');
        form.reset();
        // Reset to default values
        document.getElementById('add-schedule-frequency').value = 'daily';
        updateScheduleFields('add');
        loadJobs();
        loadStats();
        showMessage('Job added successfully! The grumbo is ready to process your data! 🚀', 'success');
    } catch (error) {
        showMessage('Failed to add job: ' + error.message, 'error');
    }
}

async function showEditJobModal(jobId) {
    try {
        const job = await apiCall(`/api/jobs/${jobId}`);
        const clients = await apiCall('/api/clients');
        
        document.getElementById('edit-job-id').value = job.id;
        document.getElementById('edit-job-name').value = job.name;
        document.getElementById('edit-source-path-input').value = job.source_path;
        document.getElementById('edit-job-enabled').checked = job.enabled;
        
        // Parse the schedule into UI components
        parseScheduleToUI(job.schedule, 'edit');
        
        const select = document.getElementById('edit-job-client-select');
        select.innerHTML = '<option value="">Select a client...</option>' +
            clients.map(client => `<option value="${client.id}" ${client.id === job.client_id ? 'selected' : ''}>${escapeHtml(client.name)}</option>`).join('');
        
        currentClient = job.client_id;
        currentEditMode = 'edit';
        
        document.getElementById('edit-job-modal').style.display = 'block';
    } catch (error) {
        showMessage('Failed to load job: ' + error.message, 'error');
    }
}

async function updateJob(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const jobId = formData.get('job_id');
    
    // Build schedule from UI
    const schedule = buildScheduleFromUI('edit');
    
    const data = {
        name: formData.get('name'),
        client_id: parseInt(formData.get('client_id')),
        source_path: formData.get('source_path'),
        schedule: schedule,
        enabled: formData.get('enabled') === 'on'
    };
    
    try {
        await apiCall(`/api/jobs/${jobId}`, 'PUT', data);
        closeModal('edit-job-modal');
        loadJobs();
        loadStats();
        showMessage('Job updated successfully! 🎉', 'success');
    } catch (error) {
        showMessage('Failed to update job: ' + error.message, 'error');
    }
}

async function runJob(jobId) {
    try {
        showMessage('Starting backup... The Shlami is preparing the fleeb juice! 🎨', 'success');
        const result = await apiCall(`/api/jobs/${jobId}/run`, 'POST');
        
        if (result.success) {
            showMessage(`Backup completed! The plumbus is now ready for use! Files: ${result.file_count}, Size: ${formatBytes(result.size_bytes)} 🎉`, 'success');
            loadJobs();
            loadBackups();
            loadStats();
        } else {
            showMessage('Backup failed: ' + result.error, 'error');
        }
    } catch (error) {
        showMessage('Failed to run backup: ' + error.message, 'error');
    }
}

async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job?')) {
        return;
    }
    
    try {
        await apiCall(`/api/jobs/${jobId}`, 'DELETE');
        loadJobs();
        loadStats();
        showMessage('Job deleted successfully', 'success');
    } catch (error) {
        showMessage('Failed to delete job: ' + error.message, 'error');
    }
}

async function showJobHistory(jobId) {
    try {
        const history = await apiCall(`/api/jobs/${jobId}/history`);
        const content = document.getElementById('job-history-content');
        
        if (history.length === 0) {
            content.innerHTML = '<p class="empty-message">No backup history yet.</p>';
        } else {
            content.innerHTML = `
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--border);">
                            <th style="padding: 10px; text-align: left;">Date</th>
                            <th style="padding: 10px; text-align: left;">Status</th>
                            <th style="padding: 10px; text-align: right;">Size</th>
                            <th style="padding: 10px; text-align: right;">Files</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${history.map(backup => `
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 10px;">${new Date(backup.start_time).toLocaleString()}</td>
                                <td style="padding: 10px;">
                                    <span class="status-badge status-${backup.status}">${backup.status}</span>
                                </td>
                                <td style="padding: 10px; text-align: right;">${formatBytes(backup.size_bytes)}</td>
                                <td style="padding: 10px; text-align: right;">${backup.file_count || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
        
        document.getElementById('job-details-modal').style.display = 'block';
    } catch (error) {
        showMessage('Failed to load job history: ' + error.message, 'error');
    }
}

// Backups Management
async function loadBackups() {
    try {
        const backups = await apiCall('/api/backups');
        allBackups = backups;
        displayBackups(backups);
    } catch (error) {
        console.error('Failed to load backups:', error);
        showMessage('Failed to load backups', 'error');
    }
}

function displayBackups(backups) {
    const container = document.getElementById('backups-list');
    
    if (backups.length === 0) {
        container.innerHTML = '<p class="empty-message">No backups yet. Once a Shlami shows up and rubs your data with fleeb juice, backups will appear here! 🎯</p>';
        return;
    }
    
    container.innerHTML = backups.map(backup => {
        const statusClass = `status-${backup.status}`;
        const duration = backup.end_time 
            ? Math.round((new Date(backup.end_time) - new Date(backup.start_time)) / 1000) + 's'
            : '-';
        
        // Get client ID from jobs
        const job = allJobs.find(j => j.id === backup.job_id);
        const clientId = job ? job.client_id : '';
        
        return `
            <div class="list-item" data-client-id="${clientId}">
                <div class="item-info">
                    <div class="item-title">${escapeHtml(backup.job_name)} - ${escapeHtml(backup.client_name)}</div>
                    <div class="item-meta">
                        Date: ${new Date(backup.start_time).toLocaleString()} | 
                        Duration: ${duration} | 
                        Size: ${formatBytes(backup.size_bytes)} | 
                        Files: ${backup.file_count || '-'}
                    </div>
                </div>
                <div class="item-actions">
                    <span class="status-badge ${statusClass}">${backup.status}</span>
                    ${backup.status === 'completed' ? 
                        `<button class="btn btn-secondary btn-sm" onclick="showBackupFiles(${backup.id})">📄 Files</button>
                         <button class="btn btn-secondary btn-sm" onclick="restoreBackup(${backup.id})">↻ Restore</button>` : 
                        ''}
                </div>
            </div>
        `;
    }).join('');
}

function filterBackups() {
    const clientId = document.getElementById('backup-client-filter').value;
    if (clientId) {
        // Ensure allJobs is loaded
        if (!allJobs || allJobs.length === 0) {
            displayBackups(allBackups);
            return;
        }
        
        const filtered = allBackups.filter(backup => {
            const job = allJobs.find(j => j.id === backup.job_id);
            return job && job.client_id == clientId;
        });
        displayBackups(filtered);
    } else {
        displayBackups(allBackups);
    }
}

async function showBackupFiles(backupId) {
    try {
        const content = document.getElementById('backup-files-content');
        content.innerHTML = '<p class="loading">Loading files...</p>';
        document.getElementById('backup-files-modal').style.display = 'block';
        
        const result = await apiCall(`/api/backups/${backupId}/files`);
        
        if (!result.success) {
            content.innerHTML = `<p class="message-error">${result.error}</p>`;
            return;
        }
        
        if (result.files.length === 0) {
            content.innerHTML = '<p class="empty-message">No files found in backup</p>';
            return;
        }
        
        content.innerHTML = `
            <div class="backup-summary">
                <p><strong>Total Files:</strong> ${result.total_files}</p>
                <p><strong>Total Size:</strong> ${formatBytes(result.total_size)}</p>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="border-bottom: 2px solid var(--border); text-align: left;">
                        <th style="padding: 10px;">Name</th>
                        <th style="padding: 10px;">Path</th>
                        <th style="padding: 10px; text-align: right;">Size</th>
                        <th style="padding: 10px;">Modified</th>
                    </tr>
                </thead>
                <tbody>
                    ${result.files.map(file => `
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 10px;">${escapeHtml(file.name)}</td>
                            <td style="padding: 10px; font-family: monospace; font-size: 0.85em;">${escapeHtml(file.path)}</td>
                            <td style="padding: 10px; text-align: right;">${formatBytes(file.size)}</td>
                            <td style="padding: 10px; font-size: 0.85em;">${new Date(file.modified).toLocaleString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        document.getElementById('backup-files-content').innerHTML = `<p class="message-error">Failed to load files: ${error.message}</p>`;
    }
}

async function restoreBackup(backupId) {
    const restorePath = prompt('Enter restore path (leave empty for original location):');
    if (restorePath === null) return;
    
    try {
        showMessage('Starting restore... Repurposing the schleem! 🔄', 'success');
        const result = await apiCall(`/api/backups/${backupId}/restore`, 'POST', {
            restore_path: restorePath || null
        });
        
        if (result.success) {
            showMessage('Restore completed successfully! Your plumbus is working perfectly! 🎊', 'success');
        } else {
            showMessage('Restore failed: ' + result.error, 'error');
        }
    } catch (error) {
        showMessage('Failed to restore backup: ' + error.message, 'error');
    }
}

// File Browser
async function loadClientPaths(clientId) {
    currentClient = clientId;
}

async function showFileBrowser(mode = 'add') {
    if (!currentClient) {
        showMessage('Please select a client first', 'error');
        return;
    }
    
    currentEditMode = mode;
    currentPath = '/';
    document.getElementById('file-browser-modal').style.display = 'block';
    await browsePath('/');
}

async function browsePath(path) {
    currentPath = path;
    const fileList = document.getElementById('file-list');
    const breadcrumb = document.getElementById('breadcrumb');
    
    fileList.innerHTML = '<p class="loading">Loading...</p>';
    breadcrumb.textContent = path;
    
    try {
        const result = await apiCall(`/api/clients/${currentClient}/browse`, 'POST', { path: path });
        
        if (!result.success) {
            fileList.innerHTML = `<p class="message-error">${result.error}</p>`;
            return;
        }
        
        let html = '';
        
        // Add parent directory link if not at root
        if (path !== '/') {
            const parentPath = path.substring(0, path.lastIndexOf('/')) || '/';
            html += `
                <div class="file-item" onclick="browsePath('${parentPath}')">
                    <span class="file-icon">📁</span>
                    <span class="file-name">..</span>
                </div>
            `;
        }
        
        // Add files and directories
        result.files.forEach(file => {
            const fullPath = path === '/' ? `/${file.name}` : `${path}/${file.name}`;
            const icon = file.is_dir ? '📁' : '📄';
            const onclick = file.is_dir ? `browsePath('${fullPath}')` : '';
            const size = file.is_dir ? '' : formatBytes(file.size);
            
            html += `
                <div class="file-item" onclick="${onclick}">
                    <span class="file-icon">${icon}</span>
                    <span class="file-name">${escapeHtml(file.name)}</span>
                    <span class="file-size">${size}</span>
                </div>
            `;
        });
        
        fileList.innerHTML = html || '<p class="empty-message">Empty directory</p>';
    } catch (error) {
        fileList.innerHTML = `<p class="message-error">Failed to load directory: ${error.message}</p>`;
    }
}

function selectCurrentPath() {
    if (currentEditMode === 'edit') {
        const editInput = document.getElementById('edit-source-path-input');
        if (editInput) {
            editInput.value = currentPath;
        }
    } else {
        const addInput = document.getElementById('source-path-input');
        if (addInput) {
            addInput.value = currentPath;
        }
    }
    closeModal('file-browser-modal');
}

// Modal Functions
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Utility Functions
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showMessage(message, type) {
    // Create temporary message element
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.textContent = message;
    messageEl.style.position = 'fixed';
    messageEl.style.top = '20px';
    messageEl.style.right = '20px';
    messageEl.style.zIndex = '10000';
    messageEl.style.maxWidth = '400px';
    
    document.body.appendChild(messageEl);
    
    // Remove after 5 seconds
    setTimeout(() => {
        messageEl.remove();
    }, 5000);
}

// Schedule UI Functions
function updateScheduleFields(mode) {
    const prefix = mode === 'add' ? 'add' : 'edit';
    const frequency = document.getElementById(`${prefix}-schedule-frequency`).value;
    
    // Hide all schedule-related fields first
    document.getElementById(`${prefix}-schedule-time`).style.display = 'none';
    document.getElementById(`${prefix}-schedule-days`).style.display = 'none';
    document.getElementById(`${prefix}-schedule-day-of-month`).style.display = 'none';
    document.getElementById(`${prefix}-schedule-custom`).style.display = 'none';
    
    // Show relevant fields based on frequency
    if (frequency === 'daily') {
        document.getElementById(`${prefix}-schedule-time`).style.display = 'block';
    } else if (frequency === 'weekly') {
        document.getElementById(`${prefix}-schedule-time`).style.display = 'block';
        document.getElementById(`${prefix}-schedule-days`).style.display = 'block';
    } else if (frequency === 'monthly') {
        document.getElementById(`${prefix}-schedule-time`).style.display = 'block';
        document.getElementById(`${prefix}-schedule-day-of-month`).style.display = 'block';
    } else if (frequency === 'custom') {
        document.getElementById(`${prefix}-schedule-custom`).style.display = 'block';
    }
}

function buildScheduleFromUI(mode) {
    const prefix = mode === 'add' ? 'add' : 'edit';
    const frequency = document.getElementById(`${prefix}-schedule-frequency`).value;
    
    if (frequency === 'manual') {
        return null;
    }
    
    if (frequency === 'custom') {
        const customCron = document.getElementById(`${prefix}-schedule-cron`).value.trim();
        return customCron || null;
    }
    
    const hour = document.getElementById(`${prefix}-schedule-hour`).value;
    const minute = document.getElementById(`${prefix}-schedule-minute`).value;
    
    let cron = '';
    
    if (frequency === 'daily') {
        // Daily: minute hour * * *
        cron = `${minute} ${hour} * * *`;
    } else if (frequency === 'weekly') {
        // Weekly: minute hour * * day_of_week
        const days = Array.from(document.querySelectorAll(`#${prefix}-schedule-days input[name="schedule_day"]:checked`))
            .map(cb => cb.value);
        
        if (days.length === 0) {
            return null; // No days selected
        }
        
        cron = `${minute} ${hour} * * ${days.join(',')}`;
    } else if (frequency === 'monthly') {
        // Monthly: minute hour day * *
        const dayOfMonth = document.getElementById(`${prefix}-schedule-day-of-month`).value;
        
        if (dayOfMonth === 'last') {
            // NOTE: Standard cron doesn't support 'L' for last day of month
            // Using day 28 as a safe fallback that exists in all months
            // Users needing true last-day-of-month should use Custom mode with external tools
            cron = `${minute} ${hour} 28 * *`;
        } else {
            cron = `${minute} ${hour} ${dayOfMonth} * *`;
        }
    }
    
    return cron;
}

function parseScheduleToUI(schedule, mode) {
    const prefix = mode === 'add' ? 'add' : 'edit';
    
    if (!schedule || schedule.trim() === '') {
        document.getElementById(`${prefix}-schedule-frequency`).value = 'manual';
        updateScheduleFields(mode);
        return;
    }
    
    const parts = schedule.trim().split(/\s+/);
    if (parts.length !== 5) {
        // Invalid or custom format
        document.getElementById(`${prefix}-schedule-frequency`).value = 'custom';
        document.getElementById(`${prefix}-schedule-cron`).value = schedule;
        updateScheduleFields(mode);
        return;
    }
    
    const [minute, hour, day, month, dayOfWeek] = parts;
    
    // Set time values (use defaults for wildcards)
    document.getElementById(`${prefix}-schedule-hour`).value = hour === '*' ? DEFAULT_SCHEDULE_HOUR.toString() : hour;
    document.getElementById(`${prefix}-schedule-minute`).value = minute === '*' ? DEFAULT_SCHEDULE_MINUTE.toString() : minute;
    
    // Determine frequency type
    if (day === '*' && month === '*' && dayOfWeek === '*') {
        // Daily
        document.getElementById(`${prefix}-schedule-frequency`).value = 'daily';
    } else if (day === '*' && month === '*' && dayOfWeek !== '*') {
        // Weekly
        document.getElementById(`${prefix}-schedule-frequency`).value = 'weekly';
        
        // Check the appropriate days
        const days = dayOfWeek.split(',');
        document.querySelectorAll(`#${prefix}-schedule-days input[name="schedule_day"]`).forEach(cb => {
            cb.checked = days.includes(cb.value);
        });
    } else if (day !== '*' && month === '*' && dayOfWeek === '*') {
        // Monthly
        document.getElementById(`${prefix}-schedule-frequency`).value = 'monthly';
        document.getElementById(`${prefix}-schedule-day-of-month`).value = day;
    } else {
        // Custom
        document.getElementById(`${prefix}-schedule-frequency`).value = 'custom';
        document.getElementById(`${prefix}-schedule-cron`).value = schedule;
    }
    
    updateScheduleFields(mode);
}
