let chart;
let autoRefresh;

// =========================
// LOAD DATA
// =========================
async function loadData(url = "/api/moods") {
    try {
        const res = await fetch(url);
        const data = await res.json();

        let counts = {
            Happy: 0,
            Sad: 0,
            Angry: 0,
            Neutral: 0,
            Surprise: 0,
            Fearful: 0
        };

        let historyHTML = "";

        data.forEach(item => {
            if (counts.hasOwnProperty(item.emotion)) {
                counts[item.emotion]++;
            } else {
                counts["Neutral"]++;
            }

            historyHTML += `
                <div class="item">
                    ${item.emotion} → ${item.time}
                </div>
            `;
        });

        document.getElementById("history").innerHTML = historyHTML;

        updateChart(counts);

    } catch (err) {
        console.error("Load error:", err);
    }
}

// =========================
// FILTER
// =========================
function applyFilter() {
    clearInterval(autoRefresh);

    let type = document.getElementById("filterType").value;
    let start = document.getElementById("startDate").value;
    let end = document.getElementById("endDate").value;

    let url = "/api/moods";

    if (type) {
        url = `/api/moods/filter?type=${type}`;
    }

    if (type === "custom" && start && end) {
        url = `/api/moods/filter?type=custom&start=${start}&end=${end}`;
    }

    loadData(url);
}

// =========================
// INSIGHT
// =========================
async function loadInsight() {
    try {
        const res = await fetch("/api/insights");
        const data = await res.json();

        document.getElementById("insight").innerText = data.insight;
    } catch (err) {
        console.error("Insight error:", err);
    }
}

// =========================
// FIXED CHART
// =========================
function updateChart(counts) {

    const ctx = document.getElementById('chart').getContext('2d');

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(counts),
            datasets: [{
                label: 'Emotion Count',
                data: Object.values(counts)
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: "white" }
                }
            },
            scales: {
                x: { ticks: { color: "white" } },
                y: { ticks: { color: "white" } }
            }
        }
    });
}

// =========================
// AUTO REFRESH
// =========================
function startAutoRefresh() {
    autoRefresh = setInterval(() => {
        loadData();
        loadInsight();
    }, 5000);
}

// =========================
// INIT (FIXED)
// =========================
window.onload = function () {
    loadData();
    loadInsight();
    startAutoRefresh();
};