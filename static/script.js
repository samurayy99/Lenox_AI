// static/script.js
function submitQuery() {
    var query = document.getElementById("query").value;
    var chatHistory = document.getElementById("chat-history");

    // Perform AJAX request to send the query to the server
    fetch("/submit-query", {
        method: "POST",
        body: JSON.stringify({ query: query }),
        headers: {
            "Content-Type": "application/json"
        }
    })
        .then(response => response.json())
        .then(data => {
            // Assuming 'data' is the server's response and it contains a field 'response'
            var responseElement = document.createElement("div");
            responseElement.textContent = data.response;
            chatHistory.appendChild(responseElement);

            // Scroll to the bottom of the chat history
            chatHistory.scrollTop = chatHistory.scrollHeight;

            // Clear the input field for the next message
            document.getElementById("query").value = "";
        })
        .catch(error => console.error("Error:", error));

    // Prevent form from submitting if you're using a form
    return false;
}
