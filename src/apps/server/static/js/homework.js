// Get DOM elements
const configSelect = document.getElementById('config-select');
const codeEditor = document.getElementById('code-editor');
const runTestsBtn = document.getElementById('run-tests-btn');
const resultsTable = document.getElementById('results-table').getElementsByTagName('tbody')[0];
const resultsSummary = document.getElementById('results-summary');
const passedCount = document.getElementById('passed-count');
const failedCount = document.getElementById('failed-count');
const totalCount = document.getElementById('total-count');

// Null checks for DOM elements
if (runTestsBtn) {
    // Run tests when button is clicked
    runTestsBtn.addEventListener('click', async function() {
        const scriptText = codeEditor ? codeEditor.value.trim() : '';
        
        if (!scriptText) {
            alert('Please enter some code to test.');
            return;
        }
        
        // Show loading state
        runTestsBtn.disabled = true;
        runTestsBtn.innerHTML = '<span class="btn-icon">⏳</span> Running...';
        
        try {
            const response = await fetch('/execute_tests', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ script_text: scriptText }),
            });
            
            const data = await response.json();
            displayResults(data);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while running tests. Please try again.');
        } finally {
            // Reset button state
            runTestsBtn.disabled = false;
            runTestsBtn.innerHTML = '<span class="btn-icon">▶</span> Run Tests';
        }
    });
}

// Display test results
function displayResults(data) {
    // Show summary
    if (resultsSummary) {
        resultsSummary.classList.remove('hidden');
    }
    if (passedCount) passedCount.textContent = data.total_passed_tests || 0;
    if (failedCount) failedCount.textContent = (data.total_tests - data.total_passed_tests) || 0;
    if (totalCount) totalCount.textContent = data.total_tests || 0;
    
    // Clear existing results
    if (!resultsTable) return;
    resultsTable.innerHTML = '';
    
    if (!data.results || data.results.length === 0) {
        resultsTable.innerHTML = '<tr class="empty-row"><td colspan="5">No test results available</td></tr>';
        return;
    }
    
    // Populate table with results
    let testNum = 1;
    data.results.forEach(fileResult => {
        fileResult.tests.forEach(test => {
            const row = resultsTable.insertRow();
            
            // Test number
            const cellNum = row.insertCell(0);
            cellNum.textContent = testNum++;
            
            // Status
            const cellStatus = row.insertCell(1);
            const statusBadge = document.createElement('span');
            statusBadge.className = 'status-badge ' + getStatusClass(test.result);
            statusBadge.textContent = getStatusText(test.result);
            cellStatus.appendChild(statusBadge);
            
            // Input
            const cellInput = row.insertCell(2);
            cellInput.textContent = test.input || '(none)';
            
            // Expected
            const cellExpected = row.insertCell(3);
            cellExpected.textContent = test.expected_output || '(none)';
            
            // Actual
            const cellActual = row.insertCell(4);
            cellActual.textContent = test.output || test.error || '(none)';
        });
    });
}

// Get status class for badge styling
function getStatusClass(result) {
    if (result.includes('MATCH')) return 'passed';
    if (result.includes('TIMEOUT')) return 'timeout';
    if (result.includes('ERROR')) return 'error';
    return 'failed';
}

// Get human-readable status text
function getStatusText(result) {
    if (result.includes('MATCH')) return 'Passed';
    if (result.includes('TIMEOUT')) return 'Timeout';
    if (result.includes('ERROR')) return 'Error';
    return 'Failed';
}

// Listen for config changes
if (configSelect) {
    configSelect.addEventListener('change', function() {
        const selectedValue = configSelect.value;
        if (selectedValue) {
            console.log('Selected config:', selectedValue);
        }
    });
}