from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from analysis import analyze_all_stocks
from notifications import notify_analysis_done
from config import SCHEDULE_HOUR, SCHEDULE_MINUTE

app = Flask(__name__)
LATEST_RESULTS = []

# SCHEDULED JOB
def run_daily_analysis():
    global LATEST_RESULTS
    results, _ = analyze_all_stocks()
    LATEST_RESULTS = results
    notify_analysis_done(results)

# ROUTES
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global LATEST_RESULTS
    results, _ = analyze_all_stocks()
    LATEST_RESULTS = results

    return jsonify({
        "top_positive": results[0] if len(results) > 0 else {},
        "top_negative": results[1] if len(results) > 1 else {}
    })

@app.route("/last-results")
def last_results():
    return jsonify(LATEST_RESULTS)

@app.route("/analyze-all", methods=["POST"])
def analyze_all():
    from analysis import analyze_all_csv_stocks

    results = analyze_all_csv_stocks()

    if not results:
        return jsonify({
            "status": "empty",
            "message": "No valid stocks found"
        })

    return jsonify({
        "status": "ok",
        "data": results
    })


# APP START
if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_daily_analysis,
        "cron",
        hour=SCHEDULE_HOUR,
        minute=SCHEDULE_MINUTE
    )
    scheduler.start()

    app.run(debug=True)
