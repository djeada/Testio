export function runTests(callback) {
    const textarea = document.querySelector('textarea[name="script_text"]');
    const script_text = textarea.value;

    fetch('/execute_tests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script_text: script_text })
        })
                .then(response => response.json())
                .then(data => {
                    callback(data);
                }).catch(console.error);
}
