// app/static/quiz_logic.js

// IMPORTANT: GENERATE_QUIZ_URL and SAVE_RESULTS_URL are defined globally in quiz.html

let currentQuiz = []; 
let currentTopic = ""; 
const selectedAnswers = {}; // Global store for user selections

// DOM Element references (Updated to match quiz.html IDs)
const topicInput = document.getElementById('quiz-topic');
const inputArea = document.getElementById('topic-input');
const quizArea = document.getElementById('quiz-display');
const resultsArea = document.getElementById('results-display');
const quizForm = document.getElementById('questions-container');
const scoreElement = document.getElementById('score-text');
const answersFeedbackElement = document.getElementById('detailed-results');

// Helper for toggling visibility (uses IDs from quiz.html)
function setVisible(elementId, isVisible) {
    document.getElementById(elementId).classList.toggle('hidden', !isVisible);
}

// =======================================================
// 1. GENERATE QUIZ FUNCTION
// =======================================================

async function generateQuiz() {
    console.log("1. Generate Quiz function started.");
    
    // Check if the HTML defined the necessary URLs (assumed to be defined via global variables)
    if (typeof GENERATE_QUIZ_URL === 'undefined') {
        window.showMessage("Configuration Error", "GENERATE_QUIZ_URL is undefined. Cannot proceed.", true);
        return;
    }
    
    const topic = topicInput.value.trim();
    if (!topic) {
        // Using the global showMessage utility instead of the forbidden alert()
        window.showMessage("Input Required", "Please enter a topic to generate a quiz.", false); 
        return;
    }

    currentTopic = topic;
    
    // Update UI to show loading state
    setVisible('topic-input', false);
    setVisible('loading-state', true);
    
    try {
        const response = await fetch(GENERATE_QUIZ_URL, {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic }),
        });

        const data = await response.json();

        // Handle error responses from the server
        if (!response.ok || data.error) {
            if (response.status === 401) {
                 window.showMessage("Session Expired", "Your session has expired. Please log out and log back in.", true);
            } else {
                window.showMessage("API Error", data.error || 'Failed to connect to the AI service. Check connection.', true);
            }
            setVisible('topic-input', true); // Show input on error
            setVisible('loading-state', false);
            console.error("Quiz Generation Failed:", data.error);
            return;
        }

        // --- CRITICAL DATA PROCESSING ---
        // Convert the correct answer text (q.answer) into a numerical index (q.correct_answer_index)
        const questions = data.questions;
        questions.forEach(q => {
            // Find the index of the correct answer string within the options list
            const correctIndex = q.options.findIndex(opt => opt === q.answer);
            // This is the index the grading logic expects
            q.correct_answer_index = correctIndex; 
        });
        // --- END CRITICAL DATA PROCESSING ---
        
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
        questionBlock.className = 'bg-gray-50 p-4 rounded-lg mb-6 border border-gray-200';
        
        let html = `<p class="font-semibold text-gray-800 mb-3">Q${index + 1}: ${q.question}</p><div id="options-${index}" class="space-y-2">`;

        q.options.forEach((option, optionIndex) => {
            const inputId = `q${index}o${optionIndex}`;
            html += `
                <button id="${inputId}" data-q-index="${index}" data-o-index="${optionIndex}"
                        class="option-button w-full text-left p-3 border border-gray-300 rounded-lg transition duration-100 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500">
                    ${String.fromCharCode(65 + optionIndex)}. ${option}
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
        btn.classList.add('border-gray-300'); // Reset border color
    });

    // Select new answer
    button.classList.add('selected-answer');
    button.classList.remove('border-gray-300'); // Ensure selected style is visible

    // Store the selection
    selectedAnswers[qIndex] = oIndex;
}

// =======================================================
// 3. SUBMIT QUIZ (Corrected)
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

        // --- THIS IS THE FIX ---
        // This object now correctly uses 'q.answer' (the string)
        // and includes all data needed for saving to the DB.
        feedbackDetails.push({
            question: q.question,
            user_answer: q.options[selectedOptionIndex], 
            correct_answer: q.answer, // <-- This was the bug
            is_correct: isCorrect,
            options: q.options,
            correct_index: q.correct_answer_index,
            selected_index: selectedOptionIndex
        });
        // --- END FIX ---
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
        qDiv.className = `p-4 rounded-lg border shadow-sm ${item.is_correct ? 'bg-green-50 border-green-400' : 'bg-red-50 border-red-400'}`;
        
        let html = `<p class="font-bold text-gray-800 mb-2">Q${index + 1}: ${item.question}</p>`;
        
        // Display selected vs correct answer
        html += `<p class="text-sm">Your Answer: <strong class="${item.is_correct ? 'text-green-600' : 'text-red-600'}">${item.user_answer}</strong></p>`;
        
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
            window.showMessage("History Warning", "Failed to save results history.", false);
        } else {
            console.log("Quiz history saved successfully.");
        }

    } catch (error) {
        console.error("Network error saving results:", error);
    }
}

// =======================================================
// 6. GLOBAL EXPORTS
// =======================================================

// Export functions to the global scope for use in HTML event handlers
window.generateQuiz = generateQuiz;
window.submitQuiz = submitQuiz;