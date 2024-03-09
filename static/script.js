document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query');
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent default behavior for all Enter key presses.
            if (!e.shiftKey) {
                submitQuery(); // Call submitQuery only if Shift is not pressed.
            } else {
                // Handle the Shift+Enter case here if needed.
                // For now, it does nothing, allowing for a potential future implementation.
            }
        }
    });
});


async function submitQuery() {
    const queryInput = document.getElementById('query');
    const query = queryInput.value.trim();
    if (!query) return;

    appendMessage(query, 'user-message');
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
        appendMessage('An error occurred while fetching the response.', 'error-message');
    } finally {
        showLoadingIndicator(false);
        queryInput.value = '';
    }
}

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

function appendMessage(content, type) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(type);
    // Ersetze URLs durch klickbare Links
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    content = content.replace(urlRegex, function(url) {
        return '<a href="' + url + '" target="_blank">' + url + '</a>';
    });
    messageDiv.innerHTML = content; // Verwende innerHTML statt innerText
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

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
    if (!data || typeof data !== 'object') {
        console.error('Invalid data format:', data);
        appendMessage('Received invalid data format.', 'error-message');
        return;
    }

    if (data.hasOwnProperty('type')) {
        if (data.type === 'visual') {
            const placeholder = appendVisualizationPlaceholder();
            renderVisualization(data.content, placeholder.id);
        } else if (data.type === 'text') {
            appendMessage(data.content, 'bot-message');
        } else {
            console.error('Unexpected data type:', data.type);
            appendMessage('Received unexpected data type.', 'error-message');
        }
    } else {
        console.error('Invalid response structure: missing "type" property.');
        appendMessage('Received invalid response structure.', 'error-message');
    }
}

function renderVisualization(data) {
    let visualizationPlaceholderId = `visualization-placeholder-${visualizationCount - 1}`;
    let visualizationPlaceholder = document.getElementById(visualizationPlaceholderId);

    if (!visualizationPlaceholder) {
        console.error('Visualization placeholder not found');
        return;
    }
    visualizationPlaceholder.style.display = 'block';

    if (data.error) {
        console.error('Visualization error:', data.error);
        appendMessage(data.error, 'error-message');
        return;
    }

    // Adjust the data structure if necessary
    const plotData = data.data.map(trace => ({
        ...trace,
        mode: 'markers', // Example adjustment
    }));

    const layout = { ...{ title: 'Visualization' }, ...data.layout };
    const config = { responsive: true };

    Plotly.newPlot(visualizationPlaceholder, plotData, layout, config).catch(error => {
        console.error('Plotly rendering error:', error);
        appendMessage('An error occurred while rendering the visualization.', 'error-message');
    });
}


// visualizationPlaceholder.style.display = 'block';

// Define your visualization logic here, possibly with Plotly or another library
// For example, with Plotly:
// Plotly.newPlot(visualizationPlaceholder, data.data, data.layout).catch(error => {
//     console.error('Plotly rendering error:', error);
//     appendMessage('An error occurred while rendering the visualization.', 'error-message');
// });


function showLoadingIndicator(isLoading) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = isLoading ? 'block' : 'none';
    }
}
