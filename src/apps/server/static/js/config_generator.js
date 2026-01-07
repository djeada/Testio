// Config Generator JavaScript

// State
let testCaseCounter = 0;
let jsonData = null;

// DOM Elements
const configForm = document.getElementById('config-form');
const testCasesContainer = document.getElementById('test-cases-container');
const addTestBtn = document.getElementById('add-test-btn');
const generateBtn = document.getElementById('generate-btn');
const resetBtn = document.getElementById('reset-btn');
const copyBtn = document.getElementById('copy-btn');
const downloadBtn = document.getElementById('download-btn');
const jsonPreview = document.getElementById('json-preview');
const testCount = document.getElementById('test-count');
const validStatus = document.getElementById('valid-status');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Add first test case by default
    addTestCase();
    
    // Event listeners
    if (addTestBtn) {
        addTestBtn.addEventListener('click', addTestCase);
    }
    
    if (generateBtn) {
        generateBtn.addEventListener('click', generateJSON);
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', resetForm);
    }
    
    if (copyBtn) {
        copyBtn.addEventListener('click', copyToClipboard);
    }
    
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadJSON);
    }
});

// Add a new test case
function addTestCase() {
    testCaseCounter++;
    const testCaseId = `test-${testCaseCounter}`;
    
    const testCaseCard = document.createElement('div');
    testCaseCard.className = 'test-case-card';
    testCaseCard.id = testCaseId;
    testCaseCard.innerHTML = `
        <div class="test-case-header">
            <h3 class="test-case-title">Test Case #${testCaseCounter}</h3>
            <button type="button" class="remove-test-btn" onclick="removeTestCase('${testCaseId}')">
                <span>🗑️</span> Remove
            </button>
        </div>
        
        <div class="form-group">
            <label class="form-label">
                Input(s)
                <span class="tooltip" data-tooltip="Test inputs (one per line). Leave empty for no input">ⓘ</span>
            </label>
            <textarea name="input" class="form-textarea" placeholder="Enter test inputs (one per line)&#10;Example:&#10;Alice&#10;25"></textarea>
            <small class="form-hint">Leave empty if no input required</small>
        </div>
        
        <div class="form-group">
            <label class="form-label">
                Expected Output(s) <span class="required">*</span>
                <span class="tooltip" data-tooltip="Expected outputs (one per line)">ⓘ</span>
            </label>
            <textarea name="output" class="form-textarea" placeholder="Enter expected outputs (one per line)&#10;Example:&#10;Hello, Alice!&#10;You are 25 years old." required></textarea>
        </div>
        
        <div class="form-row">
            <div class="form-group flex-1">
                <label class="form-label">
                    Timeout (seconds) <span class="required">*</span>
                    <span class="tooltip" data-tooltip="Maximum execution time in seconds">ⓘ</span>
                </label>
                <input type="number" name="timeout" class="form-input" value="5" min="1" max="300" required>
            </div>
        </div>
        
        <div class="form-group">
            <label class="form-checkbox-group">
                <input type="checkbox" name="interleaved" class="form-checkbox">
                <span class="form-label" style="margin: 0;">
                    Interleaved I/O
                    <span class="tooltip" data-tooltip="For interactive programs that alternate between output and input">ⓘ</span>
                </span>
            </label>
        </div>
        
        <div class="form-group">
            <label class="form-checkbox-group">
                <input type="checkbox" name="unordered" class="form-checkbox">
                <span class="form-label" style="margin: 0;">
                    Unordered Output
                    <span class="tooltip" data-tooltip="For non-deterministic output where line order doesn't matter">ⓘ</span>
                </span>
            </label>
        </div>
    `;
    
    testCasesContainer.appendChild(testCaseCard);
    updateTestCount();
}

// Remove a test case
function removeTestCase(testCaseId) {
    const testCase = document.getElementById(testCaseId);
    if (testCase) {
        // Only allow removal if there's more than one test case
        const totalTestCases = testCasesContainer.querySelectorAll('.test-case-card').length;
        if (totalTestCases > 1) {
            testCase.remove();
            updateTestCount();
        } else {
            alert('At least one test case is required.');
        }
    }
}

// Update test count display
function updateTestCount() {
    const totalTests = testCasesContainer.querySelectorAll('.test-case-card').length;
    if (testCount) {
        testCount.textContent = totalTests;
    }
}

// Generate JSON from form
function generateJSON() {
    try {
        // Get basic configuration
        const path = document.getElementById('path').value.trim();
        const runCommand = document.getElementById('run_command').value.trim();
        const compileCommand = document.getElementById('compile_command').value.trim();
        
        // Validate required fields
        if (!path) {
            showMessage('error', 'Program path is required.');
            return;
        }
        
        // Build config object
        const config = {
            path: path
        };
        
        // Add compile_command if provided
        if (compileCommand) {
            config.compile_command = compileCommand;
        }
        
        // Add run_command if provided
        if (runCommand) {
            config.run_command = runCommand;
        } else if (!compileCommand) {
            // If no compile_command and no run_command, add 'command' for backward compatibility
            // User should specify at least one
        }
        
        // Collect test cases
        const tests = [];
        const testCards = testCasesContainer.querySelectorAll('.test-case-card');
        
        testCards.forEach((card, index) => {
            const inputTextarea = card.querySelector('textarea[name="input"]');
            const outputTextarea = card.querySelector('textarea[name="output"]');
            const timeoutInput = card.querySelector('input[name="timeout"]');
            const interleavedCheckbox = card.querySelector('input[name="interleaved"]');
            const unorderedCheckbox = card.querySelector('input[name="unordered"]');
            
            const inputValue = inputTextarea.value.trim();
            const outputValue = outputTextarea.value.trim();
            const timeoutValue = parseInt(timeoutInput.value);
            const interleavedValue = interleavedCheckbox.checked;
            const unorderedValue = unorderedCheckbox.checked;
            
            // Validate output
            if (!outputValue) {
                throw new Error(`Test Case #${index + 1}: Expected output is required.`);
            }
            
            // Build test object
            const test = {
                timeout: timeoutValue
            };
            
            // Parse input (array if multiple lines, string if single line, empty array if none)
            if (inputValue) {
                const inputLines = inputValue.split('\n').map(line => line.trim()).filter(line => line);
                if (inputLines.length === 1) {
                    test.input = inputLines[0];
                } else if (inputLines.length > 1) {
                    test.input = inputLines;
                } else {
                    test.input = [];
                }
            } else {
                test.input = [];
            }
            
            // Parse output (array if multiple lines, string if single line)
            const outputLines = outputValue.split('\n').map(line => line.trim()).filter(line => line);
            if (outputLines.length === 1) {
                test.output = outputLines[0];
            } else {
                test.output = outputLines;
            }
            
            // Add optional flags
            if (interleavedValue) {
                test.interleaved = true;
            }
            
            if (unorderedValue) {
                test.unordered = true;
            }
            
            tests.push(test);
        });
        
        // Add tests to config
        config.tests = tests;
        
        // Store and display JSON
        jsonData = config;
        displayJSON(config);
        
        // Enable buttons
        if (copyBtn) copyBtn.disabled = false;
        if (downloadBtn) downloadBtn.disabled = false;
        
        // Update status
        if (validStatus) {
            validStatus.textContent = '✅ Valid';
            validStatus.className = 'info-value info-valid';
        }
        
        showMessage('success', 'JSON configuration generated successfully!');
    } catch (error) {
        console.error('Error generating JSON:', error);
        showMessage('error', error.message);
        
        // Update status
        if (validStatus) {
            validStatus.textContent = '❌ Invalid';
            validStatus.className = 'info-value info-invalid';
        }
    }
}

// Display JSON in preview
function displayJSON(data) {
    const jsonString = JSON.stringify(data, null, 2);
    if (jsonPreview) {
        jsonPreview.innerHTML = `<code>${escapeHtml(jsonString)}</code>`;
    }
}

// Copy JSON to clipboard
async function copyToClipboard() {
    if (!jsonData) {
        showMessage('error', 'No JSON to copy. Generate JSON first.');
        return;
    }
    
    try {
        const jsonString = JSON.stringify(jsonData, null, 2);
        await navigator.clipboard.writeText(jsonString);
        showMessage('success', 'JSON copied to clipboard!');
        
        // Visual feedback
        if (copyBtn) {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<span>✓</span> Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
        }
    } catch (error) {
        console.error('Copy error:', error);
        showMessage('error', 'Failed to copy to clipboard.');
    }
}

// Download JSON file
function downloadJSON() {
    if (!jsonData) {
        showMessage('error', 'No JSON to download. Generate JSON first.');
        return;
    }
    
    try {
        const jsonString = JSON.stringify(jsonData, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = 'config.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showMessage('success', 'JSON file downloaded successfully!');
    } catch (error) {
        console.error('Download error:', error);
        showMessage('error', 'Failed to download JSON file.');
    }
}

// Reset form
function resetForm() {
    if (confirm('Are you sure you want to reset the form? All data will be lost.')) {
        // Clear form
        if (configForm) {
            configForm.reset();
        }
        
        // Clear test cases
        testCasesContainer.innerHTML = '';
        testCaseCounter = 0;
        
        // Add first test case
        addTestCase();
        
        // Reset preview
        jsonData = null;
        displayJSON({ path: '', tests: [] });
        
        // Disable buttons
        if (copyBtn) copyBtn.disabled = true;
        if (downloadBtn) downloadBtn.disabled = true;
        
        // Reset status
        if (validStatus) {
            validStatus.textContent = '⏳ Pending';
            validStatus.className = 'info-value info-pending';
        }
        
        showMessage('success', 'Form reset successfully!');
    }
}

// Show message
function showMessage(type, message) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    
    // Insert at the top of the form panel
    const formPanel = document.querySelector('.form-panel');
    if (formPanel) {
        formPanel.insertBefore(messageDiv, formPanel.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
