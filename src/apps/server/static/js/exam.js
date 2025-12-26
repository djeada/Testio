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
let currentSessionId = null;
let previousConfigValue = '';
let refreshInterval = null;

// Start new exam session
if (startExamBtn) {
    startExamBtn.addEventListener('click', async function() {
        if (configSelect && !configSelect.value) {
            alert('Please select a configuration file first.');
            return;
        }
        
        startExamBtn.disabled = true;
        startExamBtn.innerHTML = '<span class="btn-icon">⏳</span> Creating Session...';
        
        try {
            // Create session on the server
            const response = await fetch('/api/exam/create_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    config_data: {
                        command: "python3",
                        path: "student_program.py",
                        tests: [
                            {
                                input: ["5", "3"],
                                output: ["Hello World", "8", "15"],
                                timeout: 1
                            },
                            {
                                input: ["10", "20"],
                                output: ["Hello World", "30", "200"],
                                timeout: 1
                            },
                            {
                                input: ["0", "0"],
                                output: ["Hello World", "0", "0"],
                                timeout: 1
                            }
                        ]
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create session');
            }
            
            const result = await response.json();
            currentSessionId = result.session_id;
            const examUrl = `${window.location.origin}${result.session_url}`;
            
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
            
            // Show notification
            showNotification('Exam session started successfully!', 'success');
            
            // Start auto-refresh of results
            startAutoRefresh();
            
        } catch (error) {
            console.error('Error creating session:', error);
            showNotification('Failed to create exam session', 'error');
            startExamBtn.disabled = false;
            startExamBtn.innerHTML = '<span class="btn-icon">🚀</span> Start New Exam Session';
        }
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
    refreshBtn.addEventListener('click', async function() {
        if (!examSessionActive || !currentSessionId) {
            alert('Please start an exam session first.');
            return;
        }
        
        await refreshResults();
    });
}

// Auto-refresh functionality
function startAutoRefresh() {
    // Refresh every 10 seconds
    refreshInterval = setInterval(async () => {
        if (examSessionActive && currentSessionId) {
            await refreshResults();
        }
    }, 10000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Refresh results from server
async function refreshResults() {
    if (!currentSessionId) return;
    
    refreshBtn.innerHTML = '<span class="btn-icon">⏳</span> Refreshing...';
    refreshBtn.disabled = true;
    
    try {
        const response = await fetch(`/api/exam/submissions/${currentSessionId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch submissions');
        }
        
        const data = await response.json();
        updateResultsTable(data.submissions);
        
        // Update counters
        if (submissionsCount) {
            submissionsCount.textContent = data.total_submissions;
        }
        if (activeStudents) {
            // Count unique students
            const uniqueStudents = new Set(data.submissions.map(s => s.student_id)).size;
            activeStudents.textContent = uniqueStudents;
        }
        
    } catch (error) {
        console.error('Error refreshing results:', error);
        showNotification('Failed to refresh results', 'error');
    } finally {
        refreshBtn.innerHTML = '<span class="btn-icon">🔄</span> Refresh';
        refreshBtn.disabled = false;
    }
}

// Update results table with submissions
function updateResultsTable(submissions) {
    if (!resultsTable) return;
    
    // Clear existing rows
    resultsTable.innerHTML = '';
    
    if (submissions.length === 0) {
        resultsTable.innerHTML = '<tr class="empty-row"><td colspan="5">No submissions yet</td></tr>';
        return;
    }
    
    // Add rows for each submission
    submissions.forEach(submission => {
        const row = resultsTable.insertRow();
        
        // Student ID
        const cellStudentId = row.insertCell(0);
        cellStudentId.textContent = submission.student_id;
        
        // Status
        const cellStatus = row.insertCell(1);
        const statusBadge = document.createElement('span');
        statusBadge.className = 'status-badge submitted';
        statusBadge.textContent = 'Submitted';
        cellStatus.appendChild(statusBadge);
        
        // Score
        const cellScore = row.insertCell(2);
        const score = submission.score || 0;
        cellScore.textContent = `${score.toFixed(2)}%`;
        cellScore.style.fontWeight = '600';
        cellScore.style.color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444';
        
        // Passed / Total
        const cellTests = row.insertCell(3);
        if (submission.test_results) {
            const total = submission.test_results.length;
            const passed = submission.test_results.filter(
                r => r.result === 'ComparisonResult.MATCH'
            ).length;
            cellTests.textContent = `${passed} / ${total}`;
        } else {
            cellTests.textContent = 'N/A';
        }
        
        // Submitted At
        const cellTime = row.insertCell(4);
        const date = new Date(submission.submitted_at);
        cellTime.textContent = date.toLocaleString();
    });
}

// Export results
if (exportBtn) {
    exportBtn.addEventListener('click', async function() {
        if (!examSessionActive || !currentSessionId) {
            alert('Please start an exam session first.');
            return;
        }
        
        try {
            const response = await fetch(`/api/exam/submissions/${currentSessionId}`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch submissions');
            }
            
            const data = await response.json();
            
            // Create CSV content
            const csvContent = generateCSV(data.submissions);
            
            // Create download link
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `exam_results_${currentSessionId}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showNotification('Results exported successfully!', 'success');
            
        } catch (error) {
            console.error('Error exporting results:', error);
            showNotification('Failed to export results', 'error');
        }
    });
}

// Generate CSV from submissions
function generateCSV(submissions) {
    const headers = ['Student ID', 'Score', 'Tests Passed', 'Total Tests', 'Submitted At'];
    const rows = [headers.join(',')];
    
    submissions.forEach(submission => {
        const score = submission.score || 0;
        const total = submission.test_results ? submission.test_results.length : 0;
        const passed = submission.test_results 
            ? submission.test_results.filter(r => r.result === 'ComparisonResult.MATCH').length 
            : 0;
        
        const row = [
            submission.student_id,
            score.toFixed(2),
            passed,
            total,
            submission.submitted_at
        ];
        rows.push(row.join(','));
    });
    
    return rows.join('\n');
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
    stopAutoRefresh();
    examSessionActive = false;
    currentSessionId = null;
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
