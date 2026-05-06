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
        setTimeout(detectLive, 1500);
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

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

                ctx.drawImage(video, 0, 0);

                ctx.fillStyle = "rgba(0,0,0,0.6)";
                ctx.fillRect(0, 0, 300, 40);

                ctx.font = "20px Arial";
                ctx.fillStyle = "lime";

                let conf = parseFloat(data.confidence || 0);

                // 🔥 FRONTEND FIX
                conf = Math.max(10, Math.min(conf, 92));
                conf = conf.toFixed(1);

                ctx.fillText(
                    "Emotion: " + data.emotion + " (" + conf + "%)",
                    10,
                    25
                );

                document.getElementById("result").innerText =
                    "Emotion: " + data.emotion + " (" + conf + "%)";

                // 🔥 SAVE CONTROL
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

            });

    }, "image/jpeg");

    setTimeout(detectLive, 2500);
}
