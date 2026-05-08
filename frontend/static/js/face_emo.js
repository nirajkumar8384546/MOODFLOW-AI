let video = document.getElementById("video");
let canvas = document.getElementById("canvas");
let ctx = canvas.getContext("2d");

let isRunning = false;

let lastEmotion = "";
let lastSaveTime = 0;

// =========================
// START CAMERA
// =========================
function startCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            isRunning = true;
            // 2 second ka wait taaki camera stabilize ho jaye
            setTimeout(detectLive, 2000);
        })
        .catch(err => {
            alert("Camera access denied!");
        });
}

// =========================
// DETECTION LOOP
// =========================
function detectLive() {
    if (!isRunning) return;

    if (video.videoWidth === 0) {
        setTimeout(detectLive, 1000);
        return;
    }

    // Set canvas dimensions
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0);

    canvas.toBlob(blob => {
        let formData = new FormData();
        formData.append("image", blob);

        fetch("/face-emotion", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            // Re-draw background video
            ctx.drawImage(video, 0, 0);

            // UI Style
            ctx.fillStyle = "rgba(0,0,0,0.6)";
            ctx.fillRect(0, 0, 320, 50);

            ctx.font = "22px Arial";
            ctx.fillStyle = "lime";

            let conf = parseFloat(data.confidence || 0);

            // Handle no face or error
            if (data.emotion === "no_face" || data.emotion === "error") {
                ctx.fillStyle = "yellow";
                ctx.fillText("Scanning for Face...", 10, 35);
                document.getElementById("result").innerText = "Scanning...";
            } else {
                // Confidence normalization logic
                conf = Math.max(10, Math.min(conf, 92));
                let displayConf = conf.toFixed(1);

                ctx.fillText(
                    "Emotion: " + data.emotion + " (" + displayConf + "%)",
                    10,
                    35
                );

                document.getElementById("result").innerText = 
                    "Emotion: " + data.emotion + " (" + displayConf + "%)";

                // 🔥 SAVE CONTROL (Logic unchanged)
                let now = Date.now();
                if (
                    data.emotion !== lastEmotion &&
                    data.emotion !== "no_face" &&
                    data.emotion !== "error" &&
                    data.confidence > 50 &&
                    now - lastSaveTime > 3000
                ) {
                    lastEmotion = data.emotion;
                    lastSaveTime = now;
                }
            }

            // 🔥 NEXT PREDICTION: 2.5 seconds ka wait (Slow & Stable)
            // Isse Render crash nahi hoga aur properly scan lagega
            setTimeout(detectLive, 2500);
        })
        .catch(err => {
            console.error("Prediction failed:", err);
            // Error hone par bhi loop chalta rahe
            setTimeout(detectLive, 3000);
        });

    }, "image/jpeg");
}
