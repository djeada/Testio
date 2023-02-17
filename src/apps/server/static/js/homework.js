// Get the select element and table body
const configSelect = document.getElementById('config-select');
const resultsTable = document.getElementById('results-table').getElementsByTagName('tbody')[0];

// Listen for changes to the select element
configSelect.addEventListener('change', function() {
  // Get the selected option value
  const selectedValue = configSelect.value;

  // Fetch data from the server based on the selected value
  fetch(`/data/${selectedValue}`)
    .then(response => response.json())
    .then(data => {
      // Clear the table body
      resultsTable.innerHTML = '';

      // Populate the table with the data
      data.forEach(result => {
        const row = resultsTable.insertRow();
        const cell1 = row.insertCell(0);
        const cell2 = row.insertCell(1);
        cell1.innerHTML = result.student_id;
        cell2.innerHTML = result.score;
      });
    })
    .catch(error => console.error(error));
});