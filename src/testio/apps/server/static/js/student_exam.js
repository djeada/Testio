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

// ---------------------------------------------------------------------------
// Joining: the first test/submission claims the student ID for this browser
// and stores the token the server returns. The final submission must carry
// that token, so nobody else can submit under the same ID.
// ---------------------------------------------------------------------------

const TOKEN_STORAGE_KEY = 'testio-exam-' + SESSION_ID;

function loadJoin() {
    try {
        const saved = JSON.parse(localStorage.getItem(TOKEN_STORAGE_KEY) || 'null');
        if (saved && typeof saved.studentId === 'string' && typeof saved.token === 'string') {
            return saved;
        }
    } catch (e) {
        // Storage unavailable or corrupted: treat as not joined.
    }
    return null;
}

function saveJoin(studentId, token) {
    try {
        localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify({ studentId, token }));
    } catch (e) {
        // Private mode etc.: the token then lives only in memory.
    }
    joined = { studentId, token };
}

let joined = loadJoin();
if (joined && studentIdInput) {
    studentIdInput.value = joined.studentId;
    studentIdInput.disabled = true;
}

async function errorMessage(response, fallback) {
    try {
        const data = await response.json();
        if (typeof data.detail === 'string') return data.detail;
        if (Array.isArray(data.detail) && data.detail.length && data.detail[0].msg) {
            return data.detail.map(item => item.msg).join('; ');
        }
    } catch (e) {
        // Not JSON.
    }
    return fallback;
}

async function ensureJoined(studentId) {
    if (joined && joined.studentId === studentId) {
        return joined.token;
    }
    const response = await fetch('/api/exam/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID, student_id: studentId })
    });
    if (!response.ok) {
        throw new Error(await errorMessage(response, 'Could not join the exam'));
    }
    const data = await response.json();
    saveJoin(data.student_id, data.student_token);
    studentIdInput.value = data.student_id;
    studentIdInput.disabled = true;
    return data.student_token;
}

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
            const token = await ensureJoined(studentId);
            const response = await fetch('/api/exam/test_code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: SESSION_ID,
                    student_id: studentId,
                    student_token: token,
                    code: code
                })
            });

            if (!response.ok) {
                throw new Error(await errorMessage(response, 'Failed to test code'));
            }

            const result = await response.json();
            displayTestResults(result);
            showNotification('Code tested successfully!', 'success');

        } catch (error) {
            console.error('Error testing code:', error);
            showNotification(error.message || 'Error testing code', 'error');
        } finally {
            testCodeBtn.disabled = hasSubmitted;
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
            const token = await ensureJoined(studentId);
            const response = await fetch('/api/exam/submit_code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: SESSION_ID,
                    student_id: studentId,
                    student_token: token,
                    code: code
                })
            });

            if (!response.ok) {
                throw new Error(await errorMessage(response, 'Failed to submit code'));
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

// Display test results (pass/fail per test; the server never sends answers)
function displayTestResults(result) {
    if (!testResultsContainer || !resultsSection) return;

    // Clear previous results
    testResultsContainer.replaceChildren();

    // Show results section
    resultsSection.style.display = 'block';

    // Display score
    const scoreDisplay = document.createElement('div');
    scoreDisplay.className = 'score-display';
    const scoreValue = document.createElement('div');
    scoreValue.className = 'score-value';
    scoreValue.textContent = `${Number(result.score) || 0}%`;
    const scoreLabel = document.createElement('div');
    scoreLabel.className = 'score-label';
    scoreLabel.textContent = `${Number(result.passed_tests) || 0} / ${Number(result.total_tests) || 0} tests passed`;
    scoreDisplay.append(scoreValue, scoreLabel);
    testResultsContainer.appendChild(scoreDisplay);

    // Compiler output for the student's own code
    if (result.compile_error) {
        const compileBox = document.createElement('pre');
        compileBox.className = 'result-card failed compile-error';
        compileBox.textContent = result.compile_error;
        testResultsContainer.appendChild(compileBox);
    }

    // Display individual test results
    (result.test_results || []).forEach((test, index) => {
        const resultName = test.result_name || test.result;
        const isPassed = resultName === 'MATCH' || resultName === 'ComparisonResult.MATCH';
        const resultCard = document.createElement('div');
        resultCard.className = `result-card ${isPassed ? 'passed' : 'failed'}`;

        const header = document.createElement('div');
        header.className = 'result-header';
        const title = document.createElement('span');
        title.className = 'result-title';
        title.textContent = `Test ${index + 1}`;
        const status = document.createElement('span');
        status.className = `result-status ${isPassed ? 'passed' : 'failed'}`;
        status.textContent = isPassed ? '✅ Passed' : `❌ ${describeFailure(resultName)}`;
        header.append(title, status);
        resultCard.appendChild(header);

        testResultsContainer.appendChild(resultCard);
    });

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function describeFailure(resultName) {
    const name = String(resultName || '');
    if (name.includes('TIMEOUT')) return 'Timed out';
    if (name.includes('EXECUTION_ERROR')) return 'Runtime error';
    return 'Wrong output';
}

// Show notification (message text may come from the server: use textContent)
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;

    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';

    const iconSpan = document.createElement('span');
    iconSpan.className = 'notification-icon';
    iconSpan.textContent = icon;
    const messageSpan = document.createElement('span');
    messageSpan.className = 'notification-message';
    messageSpan.textContent = message;
    notification.append(iconSpan, messageSpan);

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
