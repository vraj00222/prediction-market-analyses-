from flask import Flask, render_template, jsonify, send_from_directory
import json
import os

app = Flask(__name__)

DATA_PATH = os.path.join(app.static_folder, "data", "analyses.json")
CHARTS_DIR = os.path.join(app.static_folder, "charts")


def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


# ── Pages ──────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── API ────────────────────────────────────────────────────────────
@app.route("/api/data")
def api_data():
    """Full dataset: overview stats + all analyses."""
    return jsonify(load_data())


@app.route("/api/overview")
def api_overview():
    """Top-level stats only."""
    data = load_data()
    return jsonify({
        "overview": data["overview"],
        "hero": data["hero"],
        "stats_bar": data["stats_bar"],
    })


@app.route("/api/analyses")
def api_analyses():
    """List of analyses (metadata only, no heavy descriptions)."""
    data = load_data()
    return jsonify([
        {
            "id": a["id"],
            "title": a["title"],
            "nav_subtitle": a["nav_subtitle"],
            "chart": a["chart"],
        }
        for a in data["analyses"]
    ])


@app.route("/api/analysis/<int:analysis_id>")
def api_analysis(analysis_id):
    """Single analysis with full detail."""
    data = load_data()
    for a in data["analyses"]:
        if a["id"] == analysis_id:
            return jsonify(a)
    return jsonify({"error": "Analysis not found"}), 404


@app.route("/charts/<path:filename>")
def serve_chart(filename):
    """Serve chart images."""
    return send_from_directory(CHARTS_DIR, filename)


# ── Run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5050)
