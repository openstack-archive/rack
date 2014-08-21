from datetime import datetime
from flask import Flask, render_template, request
import sys
import os
sys.path.append("../" + os.path.dirname(__file__))
from db import models

app = Flask(__name__)


@app.route("/", methods=["GET"])
def form():
    return render_template("form.html")


@app.route("/", methods=["POST"])
def view():
    start_datetime = request.form.get("start_datetime", None)
    end_datetime = request.form.get("end_datetime", None)
    if not start_datetime\
            or not end_datetime:
        msg = "start_datetime and end_datetime are required"
        return render_template("error.html", msg=msg)
    try:
        start_datetime = datetime.strptime(start_datetime, "%Y/%m/%d %H:%M:%S")
        end_datetime = datetime.strptime(end_datetime, "%Y/%m/%d %H:%M:%S")
    except ValueError:
        msg = "invalid datetime format"
        return render_template("error.html", msg=msg)
    forms = {
        "start_datetime": start_datetime,
        "end_datetime": end_datetime
    }

    refs = models.select_result(forms)
    scores = []
    for ref in refs:
        if ref.avg_score is not None:
            scores.append(ref.avg_score)
    if scores:
        avg_score = round(float(sum(scores) / len(scores)), 4)
    else:
        avg_score = 0
    return render_template("result.html", start_datetime=start_datetime,
                           end_datetime=end_datetime, avg_score=avg_score)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
