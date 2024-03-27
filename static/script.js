document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query');

    // Keydown event for handling query submission
    queryInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevent default behavior for Enter key press without Shift.
            await submitQuery(); // Call submitQuery only if Shift is not pressed.
        }
    });

    // Event listener for sending a message
    document.getElementById('sendButton').addEventListener('click', async () => {
        await submitQuery(); // Use submitQuery function to handle the query submission.
    });

});

async function submitQuery() {
    const queryInput = document.getElementById('query');
    const query = queryInput.value.trim();
    if (!query) return; // Exit if query is empty

    appendMessage(query, 'user-message');
    queryInput.value = ''; // Clear the input field after getting the query
    showLoadingIndicator(true);

    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`Network response was not OK. Status: ${response.status}`);
        }

        const data = await response.json();
        processResponseData(data);
    } catch (error) {
        console.error('Error fetching response:', error);
        appendMessage('Ein Fehler ist aufgetreten.', 'error-message');
    } finally {
        showLoadingIndicator(false);
    }
} // Corrected by adding the missing closing brace

let visualizationCount = 0; // Global counter for visualization elements

async function processUserInput(query) {
    if (!query) return;

    appendMessage(query, 'user-message');
    showLoadingIndicator(true);

    try {
        const action = interpretUserInput(query);
        switch (action.type) {
            case 'fetchData':
                await fetchDataAndRespond(query);
                break;
            case 'adjustVisualization':
                adjustVisualizationParameters(query);
                break;
            case 'directCommand':
                executeDirectCommand(action.command);
                break;
            case 'complexQuery':
                await handleComplexQuery(action.query);
                break;
            default:
                appendMessage('Entschuldigung, ich habe das nicht verstanden.', 'bot-message');
                break;
        }
    } catch (error) {
        console.error('Error processing user input:', error);
        appendMessage('Ein Fehler ist bei der Verarbeitung Ihrer Eingabe aufgetreten.', 'error-message');
    } finally {
        showLoadingIndicator(false);
    }
}


// Funktion zum Hochladen der Datei
async function uploadDocument() {
    const fileUpload = document.getElementById('fileUpload'); // Korrigiert 'fileInput' zu 'fileUpload'
    if (!fileUpload.files.length) {
        console.error('Keine Datei ausgewählt');
        return;
    }
    const file = fileUpload.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        // Handle response here if needed
    } catch (error) {
        console.error('Error uploading file:', error);
    }
} // Added missing closing brace here




function appendVisualizationPlaceholder() {
    let chatMessages = document.getElementById('chat-messages');
    let visualizationPlaceholder = document.createElement('div');
    visualizationPlaceholder.id = `visualization-placeholder-${visualizationCount++}`;
    visualizationPlaceholder.classList.add('visualization-placeholder', 'bot-message');
    chatMessages.appendChild(visualizationPlaceholder);
    return visualizationPlaceholder;
}

function interpretUserInput(input) {
    if (input.toLowerCase().includes("visualisiere")) {
        return { type: 'adjustVisualization' };
    } else if (input.toLowerCase().startsWith("befehl:")) {
        return { type: 'directCommand', command: input.slice(7).trim() };
    } else if (input.toLowerCase().includes("analyse") || input.toLowerCase().includes("vergleiche")) {
        return { type: 'complexQuery', query: input };
    } else {
        return { type: 'fetchData' };
    }
}


async function fetchDataAndRespond(query) {
    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`Network response was not OK. Status: ${response.status}`);
        }

        const data = await response.json();
        processResponseData(data);
    } catch (error) {
        console.error('Error fetching response:', error);
        appendMessage('Ein Fehler ist aufgetreten.', 'error-message');
    } finally {
        showLoadingIndicator(false);
    }
} 



function adjustVisualizationParameters(query) {
    appendMessage(`Visualisierungsparameter für "${query}" angepasst.`, 'bot-message');
    // Implement logic for adjusting visualization parameters based on the query
}

function executeDirectCommand(command) {
    appendMessage(`Direkter Befehl "${command}" ausgeführt.`, 'bot-message');
    // Implement logic for executing direct commands based on the command
}

async function handleComplexQuery(query) {
    appendMessage(`Komplexe Anfrage "${query}" wird verarbeitet. Bitte warten...`, 'bot-message');
    // Implement logic for handling complex queries, possibly involving specialized API endpoints
}


function processResponseData(data) {
    if (data.type === 'visual') {
        const visualizationContainer = appendVisualizationPlaceholder();
        if (visualizationContainer && data.content) {
            try {
                const visualizationData = JSON.parse(data.content);
                Plotly.newPlot(visualizationContainer, visualizationData.data, visualizationData.layout);
            } catch (e) {
                console.error('Error parsing visualization data:', e);
                appendMessage('An error occurred while rendering the visualization.', 'error-message');
            }
        } else {
            console.error('Visualization container not found or data.content is null');
            appendMessage('Visualization content is not available.', 'error-message');
        }
    } else if (data.type === 'text') {
        appendMessage(data.content, 'bot-message');
    } else if (data.type === 'error') {
        console.error('Error response received:', data.content);
        appendMessage(data.content, 'error-message');
    } else {
        console.error('Unexpected response type:', data.type);
    }
}

function appendMessage(message, className) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(className);
    // Konvertiere URLs in anklickbare Links
    const convertedMessage = convertUrlsToLinks(message);
    messageDiv.innerHTML = convertedMessage;
    chatMessages.appendChild(messageDiv);
    scrollToLatestMessage();
}

function convertUrlsToLinks(text) {
    const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    return text.replace(urlRegex, function(url) {
        return '<a href="' + url + '" target="_blank">' + url + '</a>';
    });
}

function scrollToLatestMessage() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}



function renderVisualization(data, placeholderId) {
    let visualizationPlaceholder = document.getElementById(placeholderId);
    visualizationPlaceholder.style.display = 'block';

    if (data.error) {
        console.error('Visualization error:', data.error);
        appendMessage(data.error, 'error-message');
        return;
    }

    Plotly.newPlot(visualizationPlaceholder, data.data, data.layout).catch(error => {
        console.error('Plotly rendering error:', error);
        appendMessage('An error occurred while rendering the visualization.', 'error-message');
    });
}



function showLoadingIndicator(isLoading) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        if (isLoading) {
            loadingIndicator.style.display = 'block';
        } else {
            loadingIndicator.style.display = 'none';
        }
    } 
} 