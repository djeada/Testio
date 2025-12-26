// Initialize CodeMirror editor
let codeEditor;
let useCodeMirror = false;

// Default code template constant
const DEFAULT_CODE_TEMPLATE = '# Write your code here\n# Example:\n# print("Hello, World!")\n\n';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize CodeMirror with Python mode (can be changed based on user preference)
    const textarea = document.getElementById('code-editor');
    
    // Check if CodeMirror is available (may not load if CDN is blocked)
    if (typeof CodeMirror !== 'undefined') {
        useCodeMirror = true;
        codeEditor = CodeMirror.fromTextArea(textarea, {
            mode: 'python',
            theme: 'dracula',
            lineNumbers: true,
            indentUnit: 4,
            indentWithTabs: false,
            lineWrapping: true,
            matchBrackets: true,
            autoCloseBrackets: true,
        });
        
        // Set default code template
        codeEditor.setValue(DEFAULT_CODE_TEMPLATE);
    } else {
        // Fallback to plain textarea
        textarea.value = DEFAULT_CODE_TEMPLATE;
        textarea.style.display = 'block';
        textarea.style.width = '100%';
        textarea.style.height = '400px';
        textarea.style.fontFamily = 'monospace';
        textarea.style.fontSize = '14px';
        textarea.style.padding = '10px';
    }

    // Get DOM elements
    const studentNameInput = document.getElementById('student-name');
    const problemDescInput = document.getElementById('problem-description');
    const testCodeBtn = document.getElementById('test-code-btn');
    const submitCodeBtn = document.getElementById('submit-code-btn');
    const feedbackArea = document.getElementById('feedback-area');
    const submissionStatus = document.getElementById('submission-status');

    // Check if elements exist before adding event listeners
    if (!testCodeBtn || !submitCodeBtn || !feedbackArea) {
        console.error('Required elements not found');
        return;
    }

    // Test Code Button Handler
    testCodeBtn.addEventListener('click', async function() {
        // Get code from CodeMirror or plain textarea
        const code = useCodeMirror ? codeEditor.getValue().trim() : textarea.value.trim();
        
        if (!code || code === DEFAULT_CODE_TEMPLATE.trim()) {
            showError('Please write some code before testing!');
            return;
        }

        // Disable button during testing
        testCodeBtn.disabled = true;
        testCodeBtn.innerHTML = '<span class="btn-icon">⏳</span> Testing...';

        try {
            // Send code to execute_tests endpoint
            const response = await fetch('/execute_tests', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    script_text: code
                })
            });

            if (!response.ok) {
                throw new Error('Failed to test code');
            }

            const results = await response.json();
            displayTestResults(results);
        } catch (error) {
            console.error('Error testing code:', error);
            showError('An error occurred while testing your code. Please try again.');
        } finally {
            testCodeBtn.disabled = false;
            testCodeBtn.innerHTML = '<span class="btn-icon">🧪</span> Test Code';
        }
    });

    // Submit Code Button Handler
    submitCodeBtn.addEventListener('click', async function() {
        const studentName = studentNameInput.value.trim();
        const problemDescription = problemDescInput.value.trim();
        // Get code from CodeMirror or plain textarea
        const code = useCodeMirror ? codeEditor.getValue().trim() : textarea.value.trim();

        // Validation
        if (!studentName) {
            showError('Please enter your name!');
            studentNameInput.focus();
            return;
        }

        if (!problemDescription) {
            showError('Please describe the problem your code solves!');
            problemDescInput.focus();
            return;
        }

        if (!code || code === DEFAULT_CODE_TEMPLATE.trim()) {
            showError('Please write some code before submitting!');
            return;
        }

        // Disable button during submission
        submitCodeBtn.disabled = true;
        submitCodeBtn.innerHTML = '<span class="btn-icon">⏳</span> Submitting...';

        try {
            // Send submission to server
            const response = await fetch('/student_submission', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    student_name: studentName,
                    problem_description: problemDescription,
                    code: code
                })
            });

            if (!response.ok) {
                throw new Error('Failed to submit code');
            }

            const result = await response.json();
            showSubmissionSuccess(result);
        } catch (error) {
            console.error('Error submitting code:', error);
            showSubmissionError('An error occurred while submitting your code. Please try again.');
        } finally {
            submitCodeBtn.disabled = false;
            submitCodeBtn.innerHTML = '<span class="btn-icon">📤</span> Submit to Teacher';
        }
    });
});

function displayTestResults(results) {
    const feedbackArea = document.getElementById('feedback-area');
    
    const totalTests = results.total_tests;
    const passedTests = results.total_passed_tests;
    const failedTests = totalTests - passedTests;
    const score = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0;

    let html = `
        <div class="test-summary">
            <h3 style="margin-top: 0;">Test Results Summary</h3>
            <div class="summary-stats">
                <div class="stat-item">
                    <span class="stat-value">${score}%</span>
                    <span class="stat-label">Score</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${passedTests}/${totalTests}</span>
                    <span class="stat-label">Passed</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${failedTests}</span>
                    <span class="stat-label">Failed</span>
                </div>
            </div>
        </div>
    `;

    // Display individual test results
    if (results.results && results.results.length > 0) {
        results.results.forEach((fileResult, fileIndex) => {
            if (fileResult.tests && fileResult.tests.length > 0) {
                fileResult.tests.forEach((test, testIndex) => {
                    const isPassed = test.result === 'ComparisonResult.MATCH';
                    const statusIcon = isPassed ? '✅' : '❌';
                    const statusText = isPassed ? 'Passed' : 'Failed';
                    const statusClass = isPassed ? 'passed' : 'failed';

                    html += `
                        <div class="test-result ${statusClass}">
                            <div class="test-header">
                                <span class="test-status">${statusIcon}</span>
                                <span>Test ${testIndex + 1}: ${statusText}</span>
                            </div>
                            <div class="test-details">
                                <div><strong>Expected Output:</strong></div>
                                <div class="test-output">${escapeHtml(test.expected_output || 'N/A')}</div>
                                <div><strong>Your Output:</strong></div>
                                <div class="test-output">${escapeHtml(test.output || 'N/A')}</div>
                            </div>
                        </div>
                    `;
                });
            }
        });
    }

    // Add suggestions for improvement
    if (failedTests > 0) {
        html += `
            <div class="suggestions">
                <h4>💡 Suggestions for Improvement:</h4>
                <ul>
                    <li>Check if your output matches the expected output exactly (including spaces and newlines)</li>
                    <li>Make sure your code handles all test cases correctly</li>
                    <li>Review the failed tests to understand what went wrong</li>
                    <li>Test your code with different inputs to ensure it works correctly</li>
                </ul>
            </div>
        `;
    } else if (passedTests > 0) {
        html += `
            <div class="suggestions" style="background: #d1fae5; border-left-color: #10b981;">
                <h4 style="color: #065f46;">🎉 Great job!</h4>
                <ul style="color: #047857;">
                    <li>All tests passed! Your code is working correctly.</li>
                    <li>Consider submitting your solution to your teacher for review.</li>
                </ul>
            </div>
        `;
    }

    feedbackArea.innerHTML = html;
}

function showError(message) {
    const feedbackArea = document.getElementById('feedback-area');
    feedbackArea.innerHTML = `
        <div class="suggestions" style="background: #fee2e2; border-left-color: #ef4444;">
            <h4 style="color: #991b1b;">❌ Error</h4>
            <p style="color: #991b1b; margin: 0.5rem 0 0 0;">${escapeHtml(message)}</p>
        </div>
    `;
}

function showSubmissionSuccess(result) {
    const submissionStatus = document.getElementById('submission-status');
    submissionStatus.className = 'submission-status success';
    submissionStatus.querySelector('.status-message').innerHTML = `
        ${result.message}<br>
        <small style="opacity: 0.8; margin-top: 0.5rem; display: block;">
            Submission ID: ${result.submission_id}<br>
            Submitted at: ${new Date(result.submitted_at).toLocaleString()}
        </small>
    `;
    submissionStatus.classList.remove('hidden');

    // Hide after 10 seconds
    setTimeout(() => {
        submissionStatus.classList.add('hidden');
    }, 10000);
}

function showSubmissionError(message) {
    const submissionStatus = document.getElementById('submission-status');
    submissionStatus.className = 'submission-status error';
    submissionStatus.querySelector('.status-message').textContent = message;
    submissionStatus.classList.remove('hidden');

    // Hide after 10 seconds
    setTimeout(() => {
        submissionStatus.classList.add('hidden');
    }, 10000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
