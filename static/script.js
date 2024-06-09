document.getElementById('startRecording').addEventListener('click', function () {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            let audioChunks = [];
            mediaRecorder.ondataavailable = function (event) {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async function () {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('file', audioBlob, 'recording.webm');

                try {
                    const response = await fetch('/transcribe', {
                        method: 'POST',
                        body: formData,
                    });
                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('query').value = data.transcription;
                    } else {
                        console.error('Failed to transcribe audio:', await response.text());
                    }
                    audioChunks = [];
                } catch (error) {
                    console.error('Error:', error);
                }
            };

            document.getElementById('stopRecording').addEventListener('click', function () {
                mediaRecorder.stop();
                stream.getTracks().forEach(track => track.stop());
                document.getElementById('stopRecording').disabled = true;
            });

            document.getElementById('stopRecording').disabled = false;
            mediaRecorder.start();
        })
        .catch(error => console.error('Permission denied or microphone not available:', error));
});

document.getElementById('startRecording').disabled = false;

document.getElementById('sendButton').addEventListener('click', async () => {
    await submitQuery();
});

document.getElementById('query').addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        if (!e.shiftKey) {
            await submitQuery();
        } else {
            let content = document.getElementById('query').value;
            document.getElementById('query').value = content + '\n';
        }
    }
});

async function submitQuery() {
    const queryInput = document.getElementById('query');
    const query = queryInput.value.trim();
    if (!query) return;

    appendMessage(query, 'user-message');
    queryInput.value = '';
    showLoadingIndicator(true);

    const response = await fetch('/query', {  // Corrected endpoint
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    });

    if (!response.ok) {
        console.error('Error fetching response:', response.statusText);
        appendMessage(`An error occurred: ${response.statusText}`, 'error-message');
    } else {
        const data = await response.json();
        processResponseData(data);
    }
    showLoadingIndicator(false);
}

function appendMessage(message, className, shouldIncludeAudio = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(className);

    message = convertUrlsToLinks(message);

    messageDiv.innerHTML = message;

    if (shouldIncludeAudio && className === 'bot-message') {
        const button = document.createElement('button');
        button.textContent = 'Play';
        button.onclick = () => fetchAudio(message);
        messageDiv.appendChild(button);
    }

    chatMessages.appendChild(messageDiv);
    scrollToLatestMessage();
}

document.querySelectorAll('.dropdown-content a').forEach(item => {
    item.addEventListener('click', function (e) {
        e.preventDefault();
        const predefinedQuery = this.innerText;
        document.getElementById('query').value = predefinedQuery;
        document.getElementById('query').focus();
    });
});

function handleAudioResponse(response) {
    response.blob().then(blob => {
        const audioType = blob.type;
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
    const data = { input: text, voice: "alloy" };
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
    const visualizationContainer = appendVisualizationPlaceholder();
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
    const chatMessages = document.getElementById('chat-messages');
    const visualizationPlaceholder = document.createElement('div');
    visualizationPlaceholder.classList.add('visualization-placeholder', 'bot-message');
    chatMessages.appendChild(visualizationPlaceholder);
    return visualizationPlaceholder;
}

function processResponseData(data) {
    console.log("Received data from server:", data);
    switch (data.type) {
        case 'visual':
            handleVisualResponse(data);
            break;
        case 'text':
            appendMessage(data.content, 'bot-message', true);
            break;
        case 'ai':
            appendMessage(data.content, 'bot-message');
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
