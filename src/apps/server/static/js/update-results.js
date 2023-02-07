export default function updateResults(data) {
        document.getElementById('total-tests').innerHTML = data.total_tests;
        document.getElementById('passed-tests').innerHTML = data.total_passed_tests;
        document.getElementById('passed-tests-ratio').innerHTML = ((data.total_passed_tests / data.total_tests) * 100).toFixed(2);

        /*

        {'results': [{'input': '3', 'expected_output': '6', 'output': '6', 'error': '', 'result': 'ComparisonResult.MATCH'}], 'passed_tests_ratio': 100.0}
        */

        const testResultsContainer = document.getElementById('test-results');
        testResultsContainer.innerHTML = ''; // Clear the container

        const tableHeader = document.createElement("div");
        tableHeader.className = "table-row";

        const fileNameHeader = document.createElement("div");
        fileNameHeader.innerHTML = "File";
        fileNameHeader.className = "table-item";
        tableHeader.appendChild(fileNameHeader);

        // Create headers for each test. Use the first array index to get the length
        let index = 1;
        data.results[0].tests.forEach(() => {
            const testHeader = document.createElement("div");
            testHeader.className = "table-item";
            testHeader.innerHTML = "Test " + index++;
            tableHeader.appendChild(testHeader);
        });

        testResultsContainer.appendChild(tableHeader)

        data.results.forEach((result) => {
            const row = document.createElement("div");
            row.className = "table-row";
            const fileNameElement = document.createElement("div");
            fileNameElement.innerHTML = result.name;
            fileNameElement.className = "table-item";
            row.appendChild(fileNameElement);
            result.tests.forEach((test) => {
                const testData = document.createElement("div");
                testData.className = "table-item";
                const input = document.createElement("p");
                input.innerHTML = `Input: ${test.input}`;
                const expectedOutput = document.createElement("p");
                expectedOutput.innerHTML = `Expected: ${test.expected_output}`;
                const actualOutput = document.createElement("p");
                actualOutput.innerHTML = `Actual: ${test.output}`;
                input.classList.add(test.result === "ComparisonResult.MATCH" ? "passed" : "failed");
                expectedOutput.classList.add(test.result === "ComparisonResult.MATCH" ? "passed" : "failed");
                actualOutput.classList.add(test.result === "ComparisonResult.MATCH" ? "passed" : "failed");
                testData.appendChild(input);
                testData.appendChild(expectedOutput);
                testData.appendChild(actualOutput);
                row.appendChild(testData);
            })
            testResultsContainer.appendChild(row);
        });

    }