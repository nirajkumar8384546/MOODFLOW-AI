//static/js/main.js 
// GLOBAL MODE
let selectedMode = "";

// ================================
// MODE SELECT
// ================================
function selectMode(mode) {
    selectedMode = mode;
    console.log("Mode selected:", mode);
}

// ================================
// TEXT + AUDIO ANALYSIS
// ================================
function analyzeEmotion() {

    if (!selectedMode) {
        alert("Please select a mode first!");
        return;
    }

    const textInput = document.getElementById("textInput");
    const resultBox = document.getElementById("result");

    if (!textInput || !resultBox) return;

    const text = textInput.value.trim();

    if (!text) {
        alert("Please enter some text!");
        return;
    }

    resultBox.innerHTML = "Analyzing... ⏳";

    fetch("/analyze-audio-text", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: text })
    })
        .then(res => res.json())
        .then(data => {

            if (data.error) {
                resultBox.innerHTML = "❌ " + data.error;
                return;
            }

            let resultText = "";

            if (data.text_emotion) {
                resultText += `📝 Text: <b>${data.text_emotion}</b><br>`;
            }

            if (data.audio_emotion) {
                resultText += `🎤 Audio: <b>${data.audio_emotion}</b><br>`;
            }

            if (data.final_emotion) {
                resultText += `<hr>🔥 Final Emotion: <b>${data.final_emotion}</b>`;
            }

            resultBox.innerHTML = resultText;

            // highlight effect
            resultBox.style.color = "yellow";
            setTimeout(() => {
                resultBox.style.color = "white";
            }, 400);

        })
        .catch(err => {
            console.error("Error:", err);
            resultBox.innerHTML = "❌ Server error";
        });
}

// ================================
// MENU TOGGLE (FIXED)
// ================================
function toggleMenu() {
    const menu = document.getElementById("dropdownMenu");
    if (!menu) return;

    menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

// ================================
// CLOSE MENU ON OUTSIDE CLICK
// ================================
document.addEventListener("click", function (event) {

    const menu = document.getElementById("dropdownMenu");
    const icon = document.querySelector(".menu-icon");

    if (!menu || !icon) return;

    if (!menu.contains(event.target) && !icon.contains(event.target)) {
        menu.style.display = "none";
    }
});

// ================================
// IMAGE SLIDER (IMPROVED)
// ================================
function createSlider(trackId) {

    const track = document.getElementById(trackId);
    if (!track) return;

    // prevent duplicate init
    if (track.dataset.initialized === "true") return;
    track.dataset.initialized = "true";

    let slides = track.querySelectorAll("img");
    if (slides.length === 0) return;

    let index = 1;

    const firstClone = slides[0].cloneNode(true);
    const lastClone = slides[slides.length - 1].cloneNode(true);

    track.appendChild(firstClone);
    track.insertBefore(lastClone, slides[0]);

    slides = track.querySelectorAll("img");

    const slideWidth = track.clientWidth;

    track.style.transform = `translateX(-${slideWidth}px)`;

    setInterval(() => {
        index++;
        track.style.transition = "transform 0.6s ease";
        track.style.transform = `translateX(-${index * slideWidth}px)`;
    }, 2500);

    track.addEventListener("transitionend", () => {

        if (index >= slides.length - 1) {
            track.style.transition = "none";
            index = 1;
            track.style.transform = `translateX(-${slideWidth}px)`;
        }

        if (index <= 0) {
            track.style.transition = "none";
            index = slides.length - 2;
            track.style.transform = `translateX(-${index * slideWidth}px)`;
        }
    });
}

// ================================
// INIT (SAFE LOAD)
// ================================
window.addEventListener("DOMContentLoaded", () => {

    console.log("✅ JS Loaded");

    // slider init
    createSlider("track");
    createSlider("track_1");
    createSlider("track_2");

});