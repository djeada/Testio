export function runTests(callback) {
    fetch('/execute_tests', {
            method: 'GET'
        })
                .then(response => response.json())
                .then(data => {
                    callback(data);
                }).catch(console.error);

}
