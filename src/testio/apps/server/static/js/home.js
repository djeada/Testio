// Get the button elements
const configGeneratorBtn = document.getElementById('config-generator-btn');
const studentBtn = document.getElementById('student-btn');
const homeworkBtn = document.getElementById('homework-btn');
const examBtn = document.getElementById('exam-btn');

// Navigation functions
function navigateToConfigGenerator() {
  window.location.href = '/config-generator';
}

function navigateToStudent() {
  window.location.href = '/student';
}

function navigateToHomework() {
  window.location.href = '/homework';
}

function navigateToExam() {
  window.location.href = '/exam';
}

// Add event listeners to the buttons only if they exist
if (configGeneratorBtn) {
  configGeneratorBtn.addEventListener('click', navigateToConfigGenerator);
  const configPanel = configGeneratorBtn.closest('.home__option-panel');
  if (configPanel) {
    configPanel.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        navigateToConfigGenerator();
      }
    });
  }
}

if (studentBtn) {
  studentBtn.addEventListener('click', navigateToStudent);
  // Also allow Enter key on parent panel
  const studentPanel = studentBtn.closest('.home__option-panel');
  if (studentPanel) {
    studentPanel.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        navigateToStudent();
      }
    });
  }
}

if (homeworkBtn) {
  homeworkBtn.addEventListener('click', navigateToHomework);
  const homeworkPanel = homeworkBtn.closest('.home__option-panel');
  if (homeworkPanel) {
    homeworkPanel.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        navigateToHomework();
      }
    });
  }
}

if (examBtn) {
  examBtn.addEventListener('click', navigateToExam);
  const examPanel = examBtn.closest('.home__option-panel');
  if (examPanel) {
    examPanel.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        navigateToExam();
      }
    });
  }
}

// Keyboard shortcuts for quick navigation
document.addEventListener('keydown', (e) => {
  // Alt+1 for Student, Alt+2 for Homework, Alt+3 for Exam
  if (e.altKey && !e.ctrlKey && !e.shiftKey) {
    switch (e.key) {
      case '1':
        e.preventDefault();
        navigateToStudent();
        break;
      case '2':
        e.preventDefault();
        navigateToHomework();
        break;
      case '3':
        e.preventDefault();
        navigateToExam();
        break;
    }
  }
});

// Animate stats on scroll (if in viewport)
function animateValue(element, start, end, duration) {
  if (!element) return;
  
  let startTimestamp = null;
  const suffix = element.textContent.includes('%') ? '%' : element.textContent.includes('+') ? '+' : '';
  
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const value = Math.floor(progress * (end - start) + start);
    element.textContent = value + suffix;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  
  window.requestAnimationFrame(step);
}

// Intersection Observer for animations
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
};

const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Animate the stats when they come into view
      const testsRun = document.getElementById('total-tests-run');
      const students = document.getElementById('total-students');
      const successRate = document.getElementById('success-rate');
      
      if (testsRun) animateValue(testsRun, 0, 1000, 2000);
      if (students) animateValue(students, 0, 500, 1800);
      if (successRate) animateValue(successRate, 0, 95, 1500);
      
      // Only animate once
      statsObserver.disconnect();
    }
  });
}, observerOptions);

// Observe stats section
document.addEventListener('DOMContentLoaded', () => {
  const statsSection = document.querySelector('.home__stats');
  if (statsSection) {
    statsObserver.observe(statsSection);
  }
});
