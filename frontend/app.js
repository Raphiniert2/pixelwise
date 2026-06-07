// frontend/app.js
const API_KEY = "REPLACE_ME";  // overwritten on deploy

const pad = document.getElementById("pad");
const ctx = pad.getContext("2d");
let drawing = false;

ctx.fillStyle = "#fff";
ctx.fillRect(0, 0, pad.width, pad.height);
ctx.lineWidth = 18; ctx.lineCap = "round";

pad.onmousedown = e => {
    drawing = true; ctx.beginPath();
    ctx.moveTo(e.offsetX, e.offsetY);
};
pad.onmousemove = e => {
    if (!drawing) return;
    ctx.lineTo(e.offsetX, e.offsetY); ctx.stroke();
};
pad.onmouseup = pad.onmouseleave = () => { drawing = false; };

function getPixels() {
    // Downsample 280x280 -> 28x28, invert so ink is high.
    const tmp = document.createElement("canvas");
    tmp.width = 28; tmp.height = 28;
    tmp.getContext("2d").drawImage(pad, 0, 0, 28, 28);
    const data = tmp.getContext("2d")
        .getImageData(0, 0, 28, 28).data;
    const pixels = [];
    for (let y = 0; y < 28; y++) {
        const row = [];
        for (let x = 0; x < 28; x++)
            row.push(255 - data[(y * 28 + x) * 4]);
        pixels.push(row);
    }
    return pixels;
}

async function classify() {
    const r = await fetch("/api/classify", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        body: JSON.stringify({ pixels: getPixels() })
    });
    const out = document.getElementById("result");
    if (!r.ok) { out.textContent = "Error " + r.status; return; }
    const d = await r.json();
    out.textContent = `Prediction: ${d.prediction} ` +
        `(${(d.confidence * 100).toFixed(1)}%)`;
    refresh();
}

async function refresh() {
    const r = await fetch("/api/results");
    if (!r.ok) return;
    const ul = document.getElementById("history");
    ul.innerHTML = "";
    for (const row of (await r.json()).results) {
        const li = document.createElement("li");
        li.textContent = `${row.prediction}  ` +
            `${row.confidence.toFixed(2)}  ${row.created_at}`;
        ul.appendChild(li);
    }
}

document.getElementById("classify").onclick = classify;
document.getElementById("clear").onclick = () => {
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, pad.width, pad.height);
    document.getElementById("result").textContent = "";
};
refresh();
