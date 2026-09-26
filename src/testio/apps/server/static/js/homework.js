// Get DOM elements
const configFileInput = document.getElementById('config-file');
const studentFilesInput = document.getElementById('student-files');
const runHomeworkBtn = document.getElementById('run-homework-btn');
const configFilename = document.getElementById('config-filename');
const studentsFilename = document.getElementById('students-filename');
const fileList = document.getElementById('file-list');
const resultsSummary = document.getElementById('results-summary');
const totalStudents = document.getElementById('total-students');
const avgScore = document.getElementById('avg-score');
const studentResults = document.getElementById('student-results');

let configFile = null;
let studentFiles = [];

// Handle config file selection
if (configFileInput) {
    configFileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            configFile = e.target.files[0];
            configFilename.textContent = configFile.name;
            updateButtonState();
        }
    });
}

// Handle student files selection
if (studentFilesInput) {
    studentFilesInput.addEventListener('change', function(e) {
        studentFiles = Array.from(e.target.files);
        
        if (studentFiles.length > 0) {
            studentsFilename.textContent = `${studentFiles.length} file(s) selected`;
            
            // Display file list
            fileList.innerHTML = '';
            studentFiles.forEach((file, index) => {
                // File names are user-controlled: build the DOM, don't parse HTML.
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                const nameSpan = document.createElement('span');
                nameSpan.className = 'file-name';
                nameSpan.textContent = `${index + 1}. ${file.name}`;
                const removeBtn = document.createElement('button');
                removeBtn.className = 'remove-file';
                removeBtn.dataset.index = String(index);
                removeBtn.textContent = '✕';
                fileItem.append(nameSpan, removeBtn);
                fileList.appendChild(fileItem);
            });
            
            // Add remove file handlers
            document.querySelectorAll('.remove-file').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    removeStudentFile(index);
                });
            });
        } else {
            studentsFilename.textContent = 'Choose student files (multiple)';
            fileList.innerHTML = '';
        }
        
        updateButtonState();
    });
}

// Remove a student file from the list
function removeStudentFile(index) {
    studentFiles.splice(index, 1);
    
    // Update the file input
    const dt = new DataTransfer();
    studentFiles.forEach(file => dt.items.add(file));
    studentFilesInput.files = dt.files;
    
    // Trigger change event to update UI
    studentFilesInput.dispatchEvent(new Event('change'));
}

// Update button state based on file selection
function updateButtonState() {
    if (runHomeworkBtn) {
        runHomeworkBtn.disabled = !(configFile && studentFiles.length > 0);
    }
}

// Run homework tests
if (runHomeworkBtn) {
    runHomeworkBtn.addEventListener('click', async function() {
        if (!configFile || studentFiles.length === 0) {
            alert('Please select both a configuration file and at least one student file.');
            return;
        }
        
        // Show loading state
        runHomeworkBtn.disabled = true;
        runHomeworkBtn.innerHTML = '<span class="btn-icon">⏳</span> Testing...';
        
        // Clear previous results
        if (studentResults) studentResults.innerHTML = '';
        if (resultsSummary) resultsSummary.classList.add('hidden');
        
        try {
            // Create form data
            const formData = new FormData();
            formData.append('config_file', configFile);
            studentFiles.forEach(file => {
                formData.append('student_files', file);
            });
            
            // Send request
            const response = await teacherFetch('/homework_submission', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(await responseErrorMessage(response, `Server returned ${response.status}`));
            }
            
            const data = await response.json();
            displayHomeworkResults(data);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while testing submissions: ' + (error.message || 'please check your files and try again.'));
        } finally {
            // Reset button state
            runHomeworkBtn.disabled = false;
            runHomeworkBtn.innerHTML = '<span class="btn-icon">🚀</span> Test All Submissions';
        }
    });
}

// Display homework results
function displayHomeworkResults(data) {
    // Show and update summary
    if (resultsSummary) {
        resultsSummary.classList.remove('hidden');
    }
    
    if (totalStudents) {
        totalStudents.textContent = data.total_students || 0;
    }
    
    // Calculate average score
    if (avgScore && data.student_results) {
        const totalScore = data.student_results.reduce((sum, student) => sum + student.score, 0);
        const average = data.total_students > 0 ? totalScore / data.total_students : 0;
        avgScore.textContent = `${average.toFixed(1)}%`;
    }
    
    // Display results for each student
    if (!studentResults) return;
    studentResults.innerHTML = '';
    
    if (!data.student_results || data.student_results.length === 0) {
        studentResults.innerHTML = '<div class="no-results">No results available</div>';
        return;
    }
    
    data.student_results.forEach((student, index) => {
        const studentCard = createStudentResultCard(student, index + 1);
        studentResults.appendChild(studentCard);
    });
}

// Create a result card for a student
function createStudentResultCard(student, studentNum) {
    const card = document.createElement('div');
    card.className = 'student-card';
    
    const score = Number(student.score) || 0;
    const scoreClass = score >= 70 ? 'good' : score >= 50 ? 'medium' : 'poor';
    
    // Every server-provided value is escaped: student_name is the uploaded
    // file name, and test output is produced by student code.
    card.innerHTML = `
        <div class="student-header">
            <h3 class="student-name">
                <span class="student-number">#${studentNum}</span>
                ${escapeHtml(student.student_name)}
            </h3>
            <div class="student-score ${scoreClass}">${score}%</div>
        </div>
        <div class="student-stats">
            <div class="stat-item">
                <span class="stat-label">Tests Passed:</span>
                <span class="stat-value">${escapeHtml(student.passed_tests)}/${escapeHtml(student.total_tests)}</span>
            </div>
        </div>
        <div class="test-details">
            <button class="toggle-details" data-student="${studentNum}">
                <span class="toggle-icon">▼</span> Show Test Details
            </button>
            <div class="details-content" id="details-${studentNum}" style="display: none;">
                ${createTestDetailsTable(student.test_results)}
            </div>
        </div>
    `;
    
    // Add toggle handler
    const toggleBtn = card.querySelector('.toggle-details');
    toggleBtn.addEventListener('click', function() {
        const details = card.querySelector('.details-content');
        const icon = this.querySelector('.toggle-icon');
        
        if (details.style.display === 'none') {
            details.style.display = 'block';
            icon.textContent = '▲';
            this.innerHTML = '<span class="toggle-icon">▲</span> Hide Test Details';
        } else {
            details.style.display = 'none';
            icon.textContent = '▼';
            this.innerHTML = '<span class="toggle-icon">▼</span> Show Test Details';
        }
    });
    
    return card;
}

// Create test details table
function createTestDetailsTable(testResults) {
    if (!testResults || testResults.length === 0) {
        return '<p class="no-tests">No test results available</p>';
    }
    
    let tableHTML = `
        <table class="details-table">
            <thead>
                <tr>
                    <th>Test #</th>
                    <th>Status</th>
                    <th>Input</th>
                    <th>Expected</th>
                    <th>Actual</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    testResults.forEach((test, index) => {
        const resultName = String(test.result_name || test.result || '');
        const statusClass = getStatusClass(resultName);
        const statusText = getStatusText(resultName);
        
        tableHTML += `
            <tr>
                <td>${index + 1}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td class="truncate">${escapeHtml(test.input || '(none)')}</td>
                <td class="truncate">${escapeHtml(test.expected_output || '(none)')}</td>
                <td class="truncate">${escapeHtml(test.output || test.error || '(none)')}</td>
            </tr>
        `;
    });
    
    tableHTML += `
            </tbody>
        </table>
    `;
    
    return tableHTML;
}

// Get status class for badge styling
function getStatusClass(result) {
    if (result.includes('MISMATCH')) return 'failed';
    if (result.includes('MATCH')) return 'passed';
    if (result.includes('TIMEOUT')) return 'timeout';
    if (result.includes('ERROR')) return 'error';
    return 'failed';
}

// Get human-readable status text
function getStatusText(result) {
    if (result.includes('MISMATCH')) return 'Failed';
    if (result.includes('MATCH')) return 'Passed';
    if (result.includes('TIMEOUT')) return 'Timeout';
    if (result.includes('ERROR')) return 'Error';
    return 'Failed';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    // Ensure text is a string
    if (text == null) {
        return '';
    }
    text = String(text);
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}