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

// Start new exam session
startExamBtn.addEventListener('click', function() {
    if (!configSelect.value) {
        alert('Please select a configuration file first.');
        return;
    }
    
    // Generate a unique session ID (in a real app, this would come from the server)
    const sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);
    const examUrl = `${window.location.origin}/student/${sessionId}`;
    
    examUrlText.textContent = examUrl;
    examUrlText.classList.add('active');
    examSessionActive = true;
    
    // Update button text
    startExamBtn.innerHTML = '<span class="btn-icon">✅</span> Session Active';
    startExamBtn.disabled = true;
    
    // Show notification
    showNotification('Exam session started successfully!', 'success');
});

// Copy URL to clipboard
copyUrlBtn.addEventListener('click', async function() {
    const urlText = examUrlText.textContent;
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

// Refresh results
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

// Export results
exportBtn.addEventListener('click', function() {
    if (!examSessionActive) {
        alert('Please start an exam session first.');
        return;
    }
    
    // In a real app, this would generate and download a CSV/PDF
    showNotification('Export feature coming soon!', 'info');
});

// Config selection change
configSelect.addEventListener('change', function() {
    const selectedValue = configSelect.value;
    if (selectedValue) {
        console.log('Selected config:', selectedValue);
        // Reset session if config changes
        if (examSessionActive) {
            if (confirm('Changing configuration will end the current session. Continue?')) {
                resetSession();
            } else {
                // Revert selection (would need to track previous value)
            }
        }
    }
});

// Reset exam session
function resetSession() {
    examSessionActive = false;
    examUrlText.textContent = 'No active session';
    examUrlText.classList.remove('active');
    startExamBtn.innerHTML = '<span class="btn-icon">🚀</span> Start New Exam Session';
    startExamBtn.disabled = false;
    activeStudents.textContent = '0';
    submissionsCount.textContent = '0';
    resultsTable.innerHTML = '<tr class="empty-row"><td colspan="5">Start an exam session to see results</td></tr>';
}

// Show notification
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
        <span class="notification-message">${message}</span>
    `;
    
    // Add styles dynamically
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
