// Get the button elements
const studentBtn = document.getElementById('student-btn');
const homeworkBtn = document.getElementById('homework-btn');
const examBtn = document.getElementById('exam-btn');

// Add event listeners to the buttons only if they exist
if (studentBtn) {
  studentBtn.addEventListener('click', function() {
    window.location.href = '/student';
  });
}

if (homeworkBtn) {
  homeworkBtn.addEventListener('click', function() {
    window.location.href = '/homework'; // Replace with the actual URL of the homework page
  });
}

if (examBtn) {
  examBtn.addEventListener('click', function() {
    window.location.href = '/exam'; // Replace with the actual URL of the exam page
  });
}
