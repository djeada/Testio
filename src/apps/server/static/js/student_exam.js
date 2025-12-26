// Student Exam Page JavaScript

const studentIdInput = document.getElementById('student-id-input');
const codeEditor = document.getElementById('code-editor');
const testCodeBtn = document.getElementById('test-code-btn');
const submitCodeBtn = document.getElementById('submit-code-btn');
const resultsSection = document.getElementById('results-section');
const testResultsContainer = document.getElementById('test-results-container');
const submissionModal = document.getElementById('submission-modal');
const cancelSubmitBtn = document.getElementById('cancel-submit-btn');
const confirmSubmitBtn = document.getElementById('confirm-submit-btn');

let hasSubmitted = false;

// Test code functionality
if (testCodeBtn) {
    testCodeBtn.addEventListener('click', async function() {
        const studentId = studentIdInput.value.trim();
        const code = codeEditor.value.trim();
        
        if (!studentId) {
            showNotification('Please enter your student ID', 'error');
            return;
        }
        
        if (!code) {
            showNotification('Please write some code first', 'error');
            return;
        }
        
        testCodeBtn.disabled = true;
        testCodeBtn.innerHTML = '<span class="btn-icon">⏳</span> Testing...';
        
        try {
            const response = await fetch('/api/exam/test_code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: SESSION_ID,
                    student_id: studentId,
                    code: code
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to test code');
            }
            
            const result = await response.json();
            displayTestResults(result);
            showNotification('Code tested successfully!', 'success');
            
        } catch (error) {
            console.error('Error testing code:', error);
            showNotification(error.message || 'Error testing code', 'error');
        } finally {
            testCodeBtn.disabled = false;
            testCodeBtn.innerHTML = '<span class="btn-icon">🧪</span> Test Code';
        }
    });
}

// Submit code functionality
if (submitCodeBtn) {
    submitCodeBtn.addEventListener('click', function() {
        const studentId = studentIdInput.value.trim();
        const code = codeEditor.value.trim();
        
        if (!studentId) {
            showNotification('Please enter your student ID', 'error');
            return;
        }
        
        if (!code) {
            showNotification('Please write some code first', 'error');
            return;
        }
        
        if (hasSubmitted) {
            showNotification('You have already submitted your code', 'error');
            return;
        }
        
        // Show confirmation modal
        submissionModal.classList.add('show');
    });
}

// Cancel submission
if (cancelSubmitBtn) {
    cancelSubmitBtn.addEventListener('click', function() {
        submissionModal.classList.remove('show');
    });
}

// Confirm submission
if (confirmSubmitBtn) {
    confirmSubmitBtn.addEventListener('click', async function() {
        submissionModal.classList.remove('show');
        
        const studentId = studentIdInput.value.trim();
        const code = codeEditor.value.trim();
        
        submitCodeBtn.disabled = true;
        submitCodeBtn.innerHTML = '<span class="btn-icon">⏳</span> Submitting...';
        
        try {
            const response = await fetch('/api/exam/submit_code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: SESSION_ID,
                    student_id: studentId,
                    code: code
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to submit code');
            }
            
            const result = await response.json();
            hasSubmitted = true;
            
            displayTestResults(result);
            showNotification('Code submitted successfully!', 'success');
            
            // Disable editing after submission
            codeEditor.disabled = true;
            studentIdInput.disabled = true;
            testCodeBtn.disabled = true;
            submitCodeBtn.innerHTML = '<span class="btn-icon">✅</span> Submitted';
            
        } catch (error) {
            console.error('Error submitting code:', error);
            showNotification(error.message || 'Error submitting code', 'error');
            submitCodeBtn.disabled = false;
            submitCodeBtn.innerHTML = '<span class="btn-icon">✅</span> Submit Final Answer';
        }
    });
}

// Display test results
function displayTestResults(result) {
    if (!testResultsContainer || !resultsSection) return;
    
    // Clear previous results
    testResultsContainer.innerHTML = '';
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Display score
    const scoreDisplay = document.createElement('div');
    scoreDisplay.className = 'score-display';
    scoreDisplay.innerHTML = `
        <div class="score-value">${result.score}%</div>
        <div class="score-label">${result.passed_tests} / ${result.total_tests} tests passed</div>
    `;
    testResultsContainer.appendChild(scoreDisplay);
    
    // Display individual test results
    result.test_results.forEach((test, index) => {
        const isPassed = test.result === 'ComparisonResult.MATCH';
        const resultCard = document.createElement('div');
        resultCard.className = `result-card ${isPassed ? 'passed' : 'failed'}`;
        
        resultCard.innerHTML = `
            <div class="result-header">
                <span class="result-title">Test ${index + 1}</span>
                <span class="result-status ${isPassed ? 'passed' : 'failed'}">
                    ${isPassed ? '✅ Passed' : '❌ Failed'}
                </span>
            </div>
            <div class="result-details">
                Execution time: ${test.execution_time ? test.execution_time.toFixed(3) : 'N/A'}s
            </div>
        `;
        
        testResultsContainer.appendChild(resultCard);
    });
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Show notification
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    
    notification.innerHTML = `
        <span class="notification-icon">${icon}</span>
        <span class="notification-message">${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Close modal on outside click
if (submissionModal) {
    submissionModal.addEventListener('click', function(e) {
        if (e.target === submissionModal) {
            submissionModal.classList.remove('show');
        }
    });
}
