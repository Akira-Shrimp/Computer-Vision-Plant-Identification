/**
 * Plant Vision — Dashboard JavaScript
 * Real-time WebSocket updates, Chart.js growth tracking, and UI interactions.
 */

// ── State ────────────────────────────────────────────────────
const state = {
    connected: false,
    detectionHistory: [],
    maxDetectionItems: 50,
};

// ── Socket.IO Connection ─────────────────────────────────────
const socket = io();

socket.on("connect", () => {
    state.connected = true;
    updateConnectionStatus("connected", "Connected");
    showToast("success", "🟢 Connected to Plant Vision server");
    loadInitialData();
});

socket.on("disconnect", () => {
    state.connected = false;
    updateConnectionStatus("disconnected", "Disconnected");
    showToast("error", "🔴 Connection lost. Reconnecting...");
});

socket.on("connect_error", () => {
    updateConnectionStatus("disconnected", "Connection Error");
});

// ── Real-time Stats Updates ──────────────────────────────────
socket.on("stats_update", (data) => {
    updateUptime(data.uptime);
    updatePredictions(data.predictions);
    updateGrowthData(data.growth);
    updateRobotStatus(data.robot);
});

socket.on("snapshot_taken", (snapshot) => {
    showToast("success", `📸 Snapshot captured! Ripe ratio: ${(snapshot.ripe_ratio * 100).toFixed(1)}%`);
    const el = document.getElementById("snapshot-count");
    if (el) el.textContent = parseInt(el.textContent || 0) + 1;
});

socket.on("robot_status", (status) => {
    updateRobotStatus(status);
});

// ── Initial Data Load ────────────────────────────────────────
async function loadInitialData() {
    try {
        // Load config
        const configRes = await fetch("/api/config");
        const config = await configRes.json();
        updateSystemInfo(config);

        // Load initial stats
        const statsRes = await fetch("/api/stats");
        const stats = await statsRes.json();
        updateUptime(stats.uptime_formatted);
        updateGrowthData(stats.growth);
        updateRobotStatus(stats.robot);
        updatePredictions(stats.predictions);
    } catch (err) {
        console.error("Failed to load initial data:", err);
    }
}

// ── UI Update Functions ──────────────────────────────────────

function updateConnectionStatus(status, text) {
    const el = document.getElementById("connection-status");
    el.className = `status-pill ${status}`;
    el.querySelector(".status-text").textContent = text;
}

function updateUptime(formatted) {
    const el = document.getElementById("uptime");
    if (el && formatted) el.textContent = formatted;
}

function updatePredictions(predictions) {
    if (!predictions || !Array.isArray(predictions)) return;

    // Update detection count stat
    const countEl = document.getElementById("detection-count");
    if (countEl) countEl.textContent = predictions.length;

    // Update detection feed
    if (predictions.length > 0) {
        const now = new Date().toLocaleTimeString("vi-VN");
        predictions.forEach(pred => {
            state.detectionHistory.unshift({
                ...pred,
                time: now,
            });
        });
        // Trim history
        state.detectionHistory = state.detectionHistory.slice(0, state.maxDetectionItems);
        renderDetectionList();
    }
}

function renderDetectionList() {
    const container = document.getElementById("detection-list");
    if (!container || state.detectionHistory.length === 0) return;

    container.innerHTML = state.detectionHistory.map(det => {
        const cls = det.class || "unknown";
        const isRipe = cls.includes("ripe") || cls.includes("chin");
        const dotClass = isRipe ? "ripe" : "green";
        const conf = det.confidence ? `${(det.confidence * 100).toFixed(0)}%` : "—";
        const x = det.x ? det.x.toFixed(0) : "—";
        const y = det.y ? det.y.toFixed(0) : "—";
        const displayName = cls.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());

        return `
            <div class="detection-item">
                <div class="detection-dot ${dotClass}"></div>
                <div class="detection-info">
                    <div class="detection-class">${displayName}</div>
                    <div class="detection-coords">X: ${x} · Y: ${y}</div>
                </div>
                <div class="detection-conf">${conf}</div>
                <div class="detection-time">${det.time}</div>
            </div>
        `;
    }).join("");
}

function updateGrowthData(growth) {
    if (!growth) return;

    // Update ripe ratio stat
    const current = growth.current;
    if (current) {
        const ratioEl = document.getElementById("ripe-ratio");
        if (ratioEl) ratioEl.textContent = `${(current.ripe_ratio * 100).toFixed(1)}%`;
    }

    // Update snapshot count
    const snapEl = document.getElementById("snapshot-count");
    if (snapEl) snapEl.textContent = growth.snapshots_count || 0;

    // Update trend badge
    const trendBadge = document.getElementById("growth-trend-badge");
    if (trendBadge && growth.trend) {
        const trendMap = {
            improving: { text: "📈 Improving", cls: "improving" },
            declining: { text: "📉 Declining", cls: "declining" },
            stable: { text: "➡️ Stable", cls: "stable" },
            insufficient_data: { text: "⏳ Collecting...", cls: "" },
        };
        const t = trendMap[growth.trend] || trendMap.insufficient_data;
        trendBadge.textContent = t.text;
        trendBadge.className = `trend-badge ${t.cls}`;
    }

    // Update chart
    if (growth.history && growth.history.length > 0) {
        updateGrowthChart(growth.history);
    }
}

function updateRobotStatus(robot) {
    if (!robot) return;

    // Status
    const statusEl = document.getElementById("robot-status-text");
    if (statusEl) {
        if (robot.simulation) {
            statusEl.innerHTML = '<span class="status-dot simulation"></span> Simulation';
        } else if (robot.connected) {
            statusEl.innerHTML = '<span class="status-dot online"></span> Online';
        } else {
            statusEl.innerHTML = '<span class="status-dot offline"></span> Offline';
        }
    }

    // Mode
    const modeEl = document.getElementById("robot-mode");
    if (modeEl) modeEl.textContent = robot.simulation ? "Simulation" : "Live";

    // Port
    const portEl = document.getElementById("robot-port");
    if (portEl) portEl.textContent = robot.port || "—";

    // Commands sent
    const cmdsEl = document.getElementById("robot-commands");
    if (cmdsEl) cmdsEl.textContent = robot.commands_sent || 0;

    // Last command
    const lastCmdEl = document.getElementById("robot-last-cmd");
    if (lastCmdEl) lastCmdEl.textContent = robot.last_command || "—";

    // Last coordinates
    const coordsEl = document.getElementById("robot-last-coords");
    if (coordsEl) {
        if (robot.last_coordinates) {
            const c = robot.last_coordinates;
            coordsEl.textContent = `X: ${c.x}, Y: ${c.y}${c.z !== null ? `, Z: ${c.z}` : ""}`;
        } else {
            coordsEl.textContent = "—";
        }
    }
}

function updateSystemInfo(config) {
    if (!config) return;

    const fields = {
        "sys-camera": config.camera,
        "sys-confidence": `${(config.confidence_threshold * 100).toFixed(0)}%`,
        "sys-classes": config.target_classes ? config.target_classes.join(", ") : "—",
        "sys-interval": config.growth_interval ? `${config.growth_interval}s` : "—",
    };

    for (const [id, value] of Object.entries(fields)) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }
}

// ── Growth Chart (Chart.js) ──────────────────────────────────
let growthChart = null;

function initGrowthChart() {
    const ctx = document.getElementById("growth-chart");
    if (!ctx) return;

    growthChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "Ripe Ratio",
                    data: [],
                    borderColor: "rgba(34, 197, 94, 1)",
                    backgroundColor: "rgba(34, 197, 94, 0.1)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointBackgroundColor: "rgba(34, 197, 94, 1)",
                    pointBorderColor: "#0a0e14",
                    pointBorderWidth: 2,
                },
                {
                    label: "Total Fruits",
                    data: [],
                    borderColor: "rgba(59, 130, 246, 0.8)",
                    backgroundColor: "rgba(59, 130, 246, 0.05)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointBackgroundColor: "rgba(59, 130, 246, 1)",
                    pointBorderColor: "#0a0e14",
                    pointBorderWidth: 2,
                    yAxisID: "y1",
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: "top",
                    labels: {
                        color: "#8b95a5",
                        font: { family: "'Inter', sans-serif", size: 11 },
                        boxWidth: 12,
                        boxHeight: 12,
                        borderRadius: 3,
                        useBorderRadius: true,
                        padding: 16,
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(17, 24, 32, 0.95)",
                    titleColor: "#e8ecf1",
                    bodyColor: "#8b95a5",
                    borderColor: "rgba(255, 255, 255, 0.08)",
                    borderWidth: 1,
                    cornerRadius: 8,
                    titleFont: { family: "'Inter', sans-serif", weight: 600 },
                    bodyFont: { family: "'Inter', sans-serif" },
                    padding: 12,
                },
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: "rgba(255, 255, 255, 0.03)",
                        drawBorder: false,
                    },
                    ticks: {
                        color: "#5a6476",
                        font: { size: 10 },
                        maxTicksLimit: 10,
                    },
                },
                y: {
                    display: true,
                    position: "left",
                    min: 0,
                    max: 1,
                    grid: {
                        color: "rgba(255, 255, 255, 0.03)",
                        drawBorder: false,
                    },
                    ticks: {
                        color: "#5a6476",
                        font: { size: 10 },
                        callback: (v) => `${(v * 100).toFixed(0)}%`,
                    },
                    title: {
                        display: true,
                        text: "Ripe %",
                        color: "#5a6476",
                        font: { size: 10 },
                    },
                },
                y1: {
                    display: true,
                    position: "right",
                    grid: { drawOnChartArea: false },
                    ticks: {
                        color: "#5a6476",
                        font: { size: 10 },
                    },
                    title: {
                        display: true,
                        text: "Count",
                        color: "#5a6476",
                        font: { size: 10 },
                    },
                },
            },
        },
    });
}

function updateGrowthChart(history) {
    if (!growthChart) initGrowthChart();
    if (!growthChart || !history) return;

    const labels = history.map((s) => {
        if (!s.timestamp) return "—";
        const d = new Date(s.timestamp);
        return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
    });
    const ripeData = history.map((s) => s.ripe_ratio || 0);
    const totalData = history.map((s) => s.total || 0);

    growthChart.data.labels = labels;
    growthChart.data.datasets[0].data = ripeData;
    growthChart.data.datasets[1].data = totalData;
    growthChart.update("none");
}

// ── Button Handlers ──────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    initGrowthChart();

    // Snapshot button
    const snapshotBtn = document.getElementById("btn-snapshot-now");
    if (snapshotBtn) {
        snapshotBtn.addEventListener("click", () => {
            socket.emit("request_snapshot");
            showToast("info", "📸 Requesting growth snapshot...");
        });
    }

    // Robot home button
    const homeBtn = document.getElementById("btn-robot-home");
    if (homeBtn) {
        homeBtn.addEventListener("click", () => {
            socket.emit("robot_home");
            showToast("warning", "🏠 Sending robot to home position...");
        });
    }

    // Screenshot button
    const screenshotBtn = document.getElementById("btn-screenshot");
    if (screenshotBtn) {
        screenshotBtn.addEventListener("click", () => {
            showToast("info", "📷 Screenshot function available in detect mode");
        });
    }
});

// ── Toast Notifications ──────────────────────────────────────
function showToast(type, message) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const iconMap = {
        success: "✅",
        error: "❌",
        warning: "⚠️",
        info: "ℹ️",
    };

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${iconMap[type] || "ℹ️"}</span>
        <span class="toast-message">${message}</span>
    `;
    container.appendChild(toast);

    // Auto-remove after animation
    setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 3200);
}
