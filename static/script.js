document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query');
    queryInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            await submitQuery();
        }
    });
    document.getElementById('sendButton').addEventListener('click', async () => {
        await submitQuery();
    });
});


async function submitQuery() {
    const queryInput = document.getElementById('query');
    const query = queryInput.value.trim();
    if (!query) return;

    appendMessage(query, 'user-message');
    queryInput.value = '';
    showLoadingIndicator(true);

    // Determine the endpoint based on query content
    let endpoint = '/query';  // Default endpoint for regular queries
    let bodyPayload = { query: query };  // Default payload

    if (query.toLowerCase().includes("search:")) {
        endpoint = '/web_search';
        bodyPayload = { query: query.replace("search:", "").trim(), detailed: true };
    } else if (query.toLowerCase().includes("say:")) {
        endpoint = '/synthesize';
        const text = query.replace("say:", "").trim();
        if (text === '') {
            appendMessage('Please provide text for synthesis.', 'error-message');
            showLoadingIndicator(false);
            return;
        }
        bodyPayload = { text: text, language: 'en' };  // Explicitly set language for clarity
    }

    console.log("Using endpoint:", endpoint, "with payload:", bodyPayload);

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyPayload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        if (endpoint === '/synthesize') {
            handleAudioResponse(response);  // Handle audio file response for TTS
        } else {
            const data = await response.json();
            processResponseData(data);  // Process regular text or search data
        }
    } catch (error) {
        console.error('Error fetching response:', error);
        appendMessage(`An error occurred: ${error.message}`, 'error-message');
    } finally {
        showLoadingIndicator(false);
    }
}


function handleAudioResponse(response) {
    response.blob().then(blob => {
        const audioType = blob.type;
        console.log('Received audio type:', audioType);
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.oncanplaythrough = () => audio.play();
        audio.onerror = () => {
            console.error('Error playing audio:', audio.error);
            appendMessage('Error playing audio.', 'error-message');
        };
        appendMessage('Playing response...', 'bot-message');
    }).catch(error => {
        console.error('Error processing audio blob:', error);
        appendMessage('Error processing audio.', 'error-message');
    });
}


function fetchAudio(text) {
    const data = { input: text, voice: "alloy" };  // Example setup, adjust as needed
    fetch('/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(response => {
        if (!response.ok) throw new Error(`Failed to fetch audio with status: ${response.status}`);
        return response.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play();
    }).catch(error => {
        console.error('Error fetching or playing audio:', error);
        appendMessage('Failed to play audio.', 'error-message');
    });
}




function handleVisualResponse(data) {
    const visualizationContainer = appendVisualizationContainer();
    if (data.content && visualizationContainer) {
        try {
            const visualizationData = JSON.parse(data.content);
            Plotly.newPlot(visualizationContainer, visualizationData.data, visualizationData.layout);
        } catch (e) {
            console.error('Error parsing visualization data:', e);
            appendMessage('An error occurred while rendering the visualization.', 'error-message');
        }
    } else {
        appendMessage('Visualization content is not available or container missing.', 'error-message');
    }
}

function appendVisualizationPlaceholder() {
    let chatMessages = document.getElementById('chat-messages');
    let visualizationPlaceholder = document.createElement('div');
    visualizationPlaceholder.classList.add('visualization-placeholder', 'bot-message');
    chatMessages.appendChild(visualizationPlaceholder);
    return visualizationPlaceholder;
}




function appendMessage(message, className, shouldIncludeAudio = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(className);
    
    // Convert URLs to clickable links and set as innerHTML for link functionality
    message = convertUrlsToLinks(message);
    messageDiv.innerHTML = message;

    if (shouldIncludeAudio && className === 'bot-message') {
        const button = document.createElement('button');
        button.textContent = 'Play';
        button.onclick = () => fetchAudio(message);
        messageDiv.appendChild(button); // Append button to the message div
    }

    chatMessages.appendChild(messageDiv);
    scrollToLatestMessage();
}

function processResponseData(data) {
    console.log("Received data from server:", data);
    switch (data.type) {
        case 'visual':
            // Corrected to use appendVisualizationPlaceholder
            const visualizationPlaceholder = appendVisualizationPlaceholder();
            if (visualizationPlaceholder && data.content) {
                try {
                    const visualizationData = JSON.parse(data.content);
                    Plotly.newPlot(visualizationPlaceholder, visualizationData.data, visualizationData.layout);
                } catch (e) {
                    console.error('Error parsing visualization data:', e);
                    appendMessage('An error occurred while rendering the visualization.', 'error-message');
                }
            } else {
                console.error('Visualization container not found or data.content is null');
                appendMessage('Visualization content is not available.', 'error-message');
            }
            break;
        case 'text':
            appendMessage(data.content, 'bot-message', true); // true indicates that audio play button should be included
            break;
        case 'error':
            console.error('Error response received:', data.content);
            appendMessage(data.content, 'error-message');
            break;
        default:
            console.error('Unexpected response type:', data.type);
            appendMessage('Received unexpected type of data from the server.', 'error-message');
            break;
    }
}


function playAudio(audioUrl) {
    const audio = new Audio(audioUrl);
    audio.play().catch(error => console.error('Error playing audio:', error));
}


function convertUrlsToLinks(text) {
    const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    return text.replace(urlRegex, url => `<a href="${url}" target="_blank">${url}</a>`);
}

function scrollToLatestMessage() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoadingIndicator(isLoading) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = isLoading ? 'block' : 'none';
}

  