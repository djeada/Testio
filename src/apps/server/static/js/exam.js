// Get DOM elements
const configSelect = document.getElementById('config-select');
const resultsTable = document.getElementById('results-table').getElementsByTagName('tbody')[0];
const startExamBtn = document.getElementById('start-exam-btn');
const examUrlText = document.getElementById('exam-url-text');
const copyUrlBtn = document.getElementById('copy-url-btn');
const refreshBtn = document.getElementById('refresh-btn');
const exportBtn = document.getElementById('export-btn');
const activeStudents = document.getElementById('active-students');
const submissionsCount = document.getElementById('submissions-count');

let examSessionActive = false;
let previousConfigValue = '';

// Start new exam session
if (startExamBtn) {
    startExamBtn.addEventListener('click', function() {
        if (configSelect && !configSelect.value) {
            alert('Please select a configuration file first.');
            return;
        }
        
        // Generate a unique session ID (in a real app, this would come from the server)
        const sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);
        const examUrl = `${window.location.origin}/student/${sessionId}`;
        
        if (examUrlText) {
            examUrlText.textContent = examUrl;
            examUrlText.classList.add('active');
        }
        examSessionActive = true;
        if (configSelect) {
            previousConfigValue = configSelect.value;
        }
        
        // Update button text
        startExamBtn.innerHTML = '<span class="btn-icon">✅</span> Session Active';
        startExamBtn.disabled = true;
        
        // Show notification
        showNotification('Exam session started successfully!', 'success');
    });
}

// Copy URL to clipboard
if (copyUrlBtn) {
    copyUrlBtn.addEventListener('click', async function() {
        const urlText = examUrlText ? examUrlText.textContent : '';
        if (urlText && urlText !== 'No active session') {
            try {
                await navigator.clipboard.writeText(urlText);
                showNotification('URL copied to clipboard!', 'success');
            } catch (err) {
                console.error('Failed to copy:', err);
                // Fallback
                const textArea = document.createElement('textarea');
                textArea.value = urlText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showNotification('URL copied to clipboard!', 'success');
            }
        }
    });
}

// Refresh results
if (refreshBtn) {
    refreshBtn.addEventListener('click', function() {
        if (!examSessionActive) {
            alert('Please start an exam session first.');
            return;
        }
        
        refreshBtn.innerHTML = '<span class="btn-icon">⏳</span> Refreshing...';
        refreshBtn.disabled = true;
        
        // Simulate fetching data (in a real app, this would call the server)
        setTimeout(() => {
            refreshBtn.innerHTML = '<span class="btn-icon">🔄</span> Refresh';
            refreshBtn.disabled = false;
            showNotification('Results refreshed!', 'info');
        }, 1000);
    });
}

// Export results
if (exportBtn) {
    exportBtn.addEventListener('click', function() {
        if (!examSessionActive) {
            alert('Please start an exam session first.');
            return;
        }
        
        showNotification('Export feature coming soon!', 'info');
    });
}

// Config selection change
if (configSelect) {
    configSelect.addEventListener('change', function() {
        const selectedValue = configSelect.value;
        if (selectedValue) {
            console.log('Selected config:', selectedValue);
            // Reset session if config changes during active session
            if (examSessionActive) {
                if (confirm('Changing configuration will end the current session. Continue?')) {
                    resetSession();
                } else {
                    // Revert to previous selection
                    configSelect.value = previousConfigValue;
                }
            }
        }
    });
}

// Reset exam session
function resetSession() {
    examSessionActive = false;
    if (examUrlText) {
        examUrlText.textContent = 'No active session';
        examUrlText.classList.remove('active');
    }
    if (startExamBtn) {
        startExamBtn.innerHTML = '<span class="btn-icon">🚀</span> Start New Exam Session';
        startExamBtn.disabled = false;
    }
    if (activeStudents) activeStudents.textContent = '0';
    if (submissionsCount) submissionsCount.textContent = '0';
    if (resultsTable) {
        resultsTable.innerHTML = '<tr class="empty-row"><td colspan="5">Start an exam session to see results</td></tr>';
    }
    previousConfigValue = '';
}

// Show notification
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';
    
    notification.innerHTML = `
        <span class="notification-icon">${icon}</span>
        <span class="notification-message">${message}</span>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${bgColor};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        z-index: 1000;
        animation: notificationSlideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'notificationSlideOut 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
