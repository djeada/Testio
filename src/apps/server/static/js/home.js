// Get the button elements
const homeworkBtn = document.getElementById('homework-btn');
const examBtn = document.getElementById('exam-btn');

// Add event listeners to the buttons
homeworkBtn.addEventListener('click', function() {
  window.location.href = '/homework'; // Replace with the actual URL of the homework page
});

examBtn.addEventListener('click', function() {
  window.location.href = '/exam'; // Replace with the actual URL of the exam page
});
