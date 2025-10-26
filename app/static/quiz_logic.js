// app/static/quiz_logic.js
// This script handles the entire frontend logic for the AI quiz generation feature.

// IMPORTANT: GENERATE_QUIZ_URL and SAVE_RESULTS_URL are defined globally in quiz.html

let currentQuiz = []; 
let currentTopic = ""; 
const selectedAnswers = {}; // Global store for user selections {qIndex: oIndex}

// DOM Element references (Assumed to be defined in quiz.html)
const topicInput = document.getElementById('quiz-topic');
const inputArea = document.getElementById('topic-input');
const quizArea = document.getElementById('quiz-display');
const resultsArea = document.getElementById('results-display');
const quizForm = document.getElementById('questions-container');
const scoreElement = document.getElementById('score-text');
const answersFeedbackElement = document.getElementById('detailed-results');

// Helper for toggling visibility (uses IDs from quiz.html)
function setVisible(elementId, isVisible) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.toggle('hidden', !isVisible);
    }
}

// =======================================================
// 1. GENERATE QUIZ FUNCTION (FETCHING DATA)
// =======================================================

async function generateQuiz() {
    console.log("1. Generate Quiz function started.");
    
    if (typeof GENERATE_QUIZ_URL === 'undefined') {
        window.showMessage("Configuration Error", "GENERATE_QUIZ_URL is undefined. Cannot proceed.", true);
        return;
    }
    
    const topic = topicInput ? topicInput.value.trim() : "";
    if (!topic) {
        window.showMessage("Input Required", "Please enter a topic to generate a quiz.", false); 
        return;
    }

    currentTopic = topic;
    
    setVisible('topic-input', false);
    setVisible('loading-state', true);
    
    try {
        const response = await fetch(GENERATE_QUIZ_URL, {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic }),
        });

        const data = await response.json();

        // Handle error responses from the server (e.g., 500, 401, or custom 'error' field)
        if (!response.ok || data.error) {
            const errorMessage = data.error || 'Failed to connect to the AI service. Check connection.';
            if (response.status === 401) {
                 window.showMessage("Session Expired", "Your session has expired. Please log out and log back in.", true);
            } else {
                 window.showMessage("API Error", errorMessage, true);
            }
            setVisible('topic-input', true);
            setVisible('loading-state', false);
            console.error("Quiz Generation Failed:", errorMessage);
            return;
        }

        // --- CRITICAL DATA PROCESSING FIX ---
        // Fix the mismatch between AI JSON object output and JS array processing
        const questions = data.questions;
        questions.forEach(q => {
            // q.options is currently an object: {"A": "Option A text", ...}
            // 1. Get the list of option texts (the values) for rendering/grading
            const optionValuesArray = Object.values(q.options); 
            
            // 2. Determine the numerical index (0, 1, 2, or 3) of the correct answer letter
            const correctLetter = q.answer; 
            
            let correctIndex = -1;
            if (correctLetter && correctLetter.length === 1) {
                // ASCII arithmetic: 'A'.charCodeAt(0) is 65, 'B' is 66, etc.
                // 'A'.charCodeAt(0) - 'A'.charCodeAt(0) = 0
                correctIndex = correctLetter.toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0);
            }

            // Reassign: q.options is now an array of text for rendering
            q.options = optionValuesArray; 
            // Add the calculated index
            q.correct_answer_index = correctIndex; 
        });
        // --- END CRITICAL DATA PROCESSING FIX ---
        
        currentQuiz = questions; 
        
        renderQuiz(data.title || `Quiz on ${currentTopic}`);

    } catch (error) {
        window.showMessage("Network Error", "Could not connect to the server or retrieve data.", true);
        setVisible('topic-input', true);
        setVisible('loading-state', false);
        console.error("Quiz Fetch Error:", error);
    }
}

// =======================================================
// 2. RENDER QUIZ & INTERACTION HANDLERS
// =======================================================

function renderQuiz(title) {
    document.getElementById('quiz-title').textContent = title;
    quizForm.innerHTML = ''; 
    Object.keys(selectedAnswers).forEach(key => delete selectedAnswers[key]); // Reset selected answers

    currentQuiz.forEach((q, index) => {
        const questionBlock = document.createElement('div');
        questionBlock.className = 'bg-gray-50 p-4 rounded-lg mb-6 border border-gray-200 fade-in'; // Added fade-in
        
        let html = `<p class="font-semibold text-gray-800 mb-3">Q${index + 1}: ${q.question}</p><div id="options-${index}" class="space-y-2">`;

        // q.options is now an array from the FIX above
        q.options.forEach((option, optionIndex) => {
            const inputId = `q${index}o${optionIndex}`;
            const optionLetter = String.fromCharCode(65 + optionIndex);
            html += `
                <button id="${inputId}" data-q-index="${index}" data-o-index="${optionIndex}"
                         class="option-button w-full text-left p-3 border border-gray-300 rounded-lg transition duration-100 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 hover:bg-gray-100">
                    <span class="font-bold mr-2 text-blue-600">${optionLetter}.</span> ${option}
                </button>
            `;
        });
        
        html += `</div>`;
        questionBlock.innerHTML = html;
        quizForm.appendChild(questionBlock);
        
        // Attach click listeners to all option buttons for this question
        q.options.forEach((_, oIndex) => {
            document.getElementById(`q${index}o${oIndex}`).addEventListener('click', handleOptionClick);
        });
    });

    setVisible('loading-state', false);
    setVisible('quiz-display', true);
}

function handleOptionClick(event) {
    const button = event.currentTarget;
    const qIndex = parseInt(button.dataset.qIndex);
    const oIndex = parseInt(button.dataset.oIndex);

    // Deselect previous selection for this question
    const optionContainer = document.getElementById(`options-${qIndex}`);
    optionContainer.querySelectorAll('.selected-answer').forEach(btn => {
        btn.classList.remove('selected-answer');
        btn.classList.remove('bg-blue-200'); // Remove background from previous
        btn.classList.add('border-gray-300'); // Reset border color
    });

    // Select new answer
    button.classList.add('selected-answer');
    button.classList.add('bg-blue-200'); // Add selection background
    button.classList.remove('border-gray-300'); // Ensure selected style is visible

    // Store the selection
    selectedAnswers[qIndex] = oIndex;
}

// =======================================================
// 3. SUBMIT QUIZ 
// =======================================================

function submitQuiz() {
    // Check if all questions have been answered
    if (Object.keys(selectedAnswers).length !== currentQuiz.length) {
        window.showMessage("Incomplete Quiz", "Please answer all questions before submitting.", false);
        return;
    }

    let score = 0;
    const totalQuestions = currentQuiz.length;
    const feedbackDetails = [];

    currentQuiz.forEach((q, index) => {
        const selectedOptionIndex = selectedAnswers[index];
        const isCorrect = selectedOptionIndex === q.correct_answer_index; 

        if (isCorrect) {
            score++;
        }

        // Gather all data needed for display and database storage
        feedbackDetails.push({
            question: q.question,
            user_answer: q.options[selectedOptionIndex], 
            correct_answer: q.options[q.correct_answer_index], // Use index to get the correct text
            is_correct: isCorrect,
            // Include full options list for comprehensive saving
            options: q.options, 
            correct_index: q.correct_answer_index,
            selected_index: selectedOptionIndex
        });
    });

    renderResults(score, totalQuestions, feedbackDetails);
    saveResultsToDatabase(score, totalQuestions, feedbackDetails);
}

// =======================================================
// 4. RENDER RESULTS (Display feedback)
// =======================================================

function renderResults(score, total, details) {
    // Update score text
    scoreElement.textContent = `${score} / ${total}`;
    
    answersFeedbackElement.innerHTML = '';
    
    details.forEach((item, index) => {
        const qDiv = document.createElement('div');
        qDiv.className = `p-4 rounded-lg border shadow-sm transition duration-300 ${item.is_correct ? 'bg-green-50 border-green-400' : 'bg-red-50 border-red-400'}`;
        
        let html = `<p class="font-bold text-gray-800 mb-2">Q${index + 1}: ${item.question}</p>`;
        
        // Display selected vs correct answer
        html += `<p class="text-sm mb-1">Your Answer: <strong class="${item.is_correct ? 'text-green-600' : 'text-red-600'}">${item.user_answer}</strong></p>`;
        
        if (!item.is_correct) {
            html += `<p class="text-sm">Correct Answer: <span class="text-indigo-700 font-semibold">${item.correct_answer}</span></p>`;
        }
        
        qDiv.innerHTML = html;
        answersFeedbackElement.appendChild(qDiv);
    });

    setVisible('quiz-display', false);
    setVisible('results-display', true);
}

// =======================================================
// 5. SAVE RESULTS TO DATABASE
// =======================================================

async function saveResultsToDatabase(score, total, detail) {
    if (typeof SAVE_RESULTS_URL === 'undefined') {
        console.error("ERROR: SAVE_RESULTS_URL is undefined. Cannot save results.");
        return;
    }
    
    const resultsPayload = {
        topic: currentTopic,
        score: score,
        total: total,
        detail: detail // 'detail' now contains all info
    };

    try {
        const res = await fetch(SAVE_RESULTS_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(resultsPayload)
        });

        const data = await res.json();
        if (!data.success) {
            console.error("Failed to save quiz history:", data.error);
            // This is a warning, not a critical crash
            window.showMessage("History Warning", "Failed to save results history.", false); 
        } else {
            console.log("Quiz history saved successfully.");
        }

    } catch (error) {
        // This catch block handles network errors during the SAVE operation
        console.error("Network error saving results:", error);
    }
}

// =======================================================
// 6. GLOBAL EXPORTS
// =======================================================

// Export functions to the global scope for use in HTML event handlers
window.generateQuiz = generateQuiz;
window.submitQuiz = submitQuiz;
// ... inside your <script> block ...

// app/static/quiz_logic.js (inside dashboard.html <script>)

// --- Notes Generator Logic (CORRECTED for Preview) ---
// --- Notes Generator Logic (CORRECTED for format and filename) ---
// --- Notes Generator Logic (FINAL CORRECTED LOGIC) ---
// --- Notes Generator Logic (Updated for Notification & History) ---
async function generateAndDownloadNotes() {
    // ... (Keep input reading, validation, and loading state setup as before) ...
    const notesInput = document.getElementById('notes-topic-input');
    const formatSelect = document.getElementById('download-format-select');

    const topic = notesInput ? notesInput.value.trim() : "";
    const requestedFormat = formatSelect ? formatSelect.value.toLowerCase() : 'docx'; 

    if (!topic) {
        alert("Please enter a topic for the notes.");
        notesInput.focus();
        return;
    }

    const mainElement = document.querySelector('main');
    const originalContentHtml = mainElement.innerHTML; 
    const loadingHtml = `
        <div class="text-center p-20">
            <h3 class="text-2xl font-semibold text-gray-700 mb-4">Generating Comprehensive Notes...</h3>
            <p class="text-gray-500 mb-4">This process may take 10-30 seconds as the AI generates detailed content.</p>
            <svg class="animate-spin h-8 w-8 text-purple-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        </div>
    `;
    mainElement.innerHTML = loadingHtml;

    try {
        const response = await fetch("{{ url_for('main.generate_notes_api') }}", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic, format: requestedFormat }) 
        });

        const data = await response.json();
        
        // --- Restore original content after fetching data ---
        mainElement.innerHTML = originalContentHtml; 

        if (!response.ok || data.error) {
            alert(`Notes Generation Failed! Error: ${data.error || 'Unknown server error.'}`);
            return;
        }

        // --- SUCCESS: Extract Data ---
        const downloadUrl = data.download_url; 
        const filename = data.filename;       
        const content = data.content_markdown; 

        if (!downloadUrl) {
            alert("Download failed: The server did not return a valid file URL.");
            return;
        }

        // --- Execute Download, Notification, and History Update ---

        // 1. Trigger Download (same as before)
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // 2. Show External Pop Notification
        showDownloadNotification(filename); 

        // 3. Update Internal Download History Log
        updateDownloadHistory(filename, downloadUrl, filename.toUpperCase().split('.').pop());
        
        // 4. Show success message (optional, as the notification handles it)
        alert(`Download initiated successfully! File: ${filename}`);
        
        // --- Final Step: Display Preview (Optional, but useful) ---
        // If you want the preview to display after download, uncomment the code below:

        /*
        let warningMessage = '';
        const actualFormat = filename.toUpperCase().split('.').pop();
        if (actualFormat !== requestedFormat.toUpperCase() && actualFormat === 'DOCX') {
             warningMessage = `
                <div class="p-3 mb-3 bg-red-100 border-l-4 border-red-500 text-red-800 text-sm">
                    <strong>Conversion Warning:</strong> Requested ${requestedFormat.toUpperCase()} but generated ${actualFormat}.
                </div>
            `;
        }
        
        const previewHtml = `<div class="p-6 bg-white rounded-lg shadow-xl lg-col-span-3">... Preview Content ...</div>`;
        mainElement.innerHTML = previewHtml; 
        */


    } catch (error) {
        // Restore content on network error
        document.querySelector('main').innerHTML = originalContentHtml; 
        console.error("Notes Download Error:", error);
        alert("A network error occurred. Please check your server connection.");
    }
}
// --- NOTIFICATION & HISTORY UTILITIES ---

function requestNotificationPermission() {
    if (!("Notification" in window)) {
        console.warn("Browser does not support desktop notifications.");
    } else if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
}

function showDownloadNotification(filename) {
    if (Notification.permission === 'granted') {
        new Notification("Download Complete", {
            body: `Your study notes (${filename}) are ready!`,
            icon: "{{ url_for('static', filename='favicon.ico') }}" // Use an existing icon path
        });
    }
}

function updateDownloadHistory(filename, url, format) {
    const log = document.getElementById('download-history-log');
    const emptyMsg = document.getElementById('empty-history-message');

    if (emptyMsg) emptyMsg.remove(); // Remove 'No downloads yet' message

    const timestamp = new Date().toLocaleTimeString();

    const entry = document.createElement('div');
    entry.className = 'flex justify-between items-center text-xs p-2 rounded-md hover:bg-gray-100 transition-colors';
    
    entry.innerHTML = `
        <span class="text-gray-700 font-medium">
            [${timestamp}] <span class="uppercase text-yellow-600">${format}</span>: ${filename}
        </span>
        <a href="${url}" download="${filename}" class="text-blue-500 hover:text-blue-700 text-right underline ml-4">
            Re-Download
        </a>
    `;
    log.prepend(entry); // Add to the top of the log
}

// --- Call Permission Request on page load (Optional: for cleaner UX) ---
document.addEventListener('DOMContentLoaded', requestNotificationPermission);