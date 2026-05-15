"""CPG Supply Chain Disruption Notifier — Main Flask Application."""

import json
import os
import sys

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for

sys.path.insert(0, os.path.dirname(__file__))

import config
from api.mock_api import mock_api
from data.synthetic_data import generate_all_sample_data, save_sample_csv
from utils.preprocessor import (
    preprocess_shipment_data,
    preprocess_inventory_data,
    preprocess_supplier_data,
    auto_detect_and_preprocess,
)
from agents.disruption_detector import run_full_detection
from agents.notification_engine import generate_notifications

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.register_blueprint(mock_api)

_notification_store = {"latest": None}


@app.route("/")
def dashboard():
    return render_template("index.html",
                           notifications=_notification_store.get("latest"),
                           use_genai=config.USE_GENAI)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        files = request.files.getlist("datafiles")
        if not files or all(f.filename == "" for f in files):
            flash("Please select at least one CSV or JSON file.", "warning")
            return redirect(url_for("upload"))

        shipment_df = inventory_df = supplier_df = None

        for f in files:
            if f.filename == "":
                continue
            content = f.read()
            df, category = auto_detect_and_preprocess(content, f.filename)

            if category == "shipment":
                shipment_df = df
            elif category == "inventory":
                inventory_df = df
            elif category == "supplier":
                supplier_df = df
            else:
                flash(f"Could not auto-detect data type for '{f.filename}'. Skipped.", "warning")

        alerts = run_full_detection(shipment_df, inventory_df, supplier_df)
        result = generate_notifications(alerts)
        _notification_store["latest"] = result

        flash(f"Analysis complete — {result['total_alerts']} disruptions detected.", "success")
        return redirect(url_for("notifications"))

    return render_template("upload.html")


@app.route("/analyze-sample", methods=["POST"])
def analyze_sample():
    shipments, inventory, suppliers = generate_all_sample_data()

    shipments = preprocess_shipment_data(shipments)
    inventory = preprocess_inventory_data(inventory)
    suppliers = preprocess_supplier_data(suppliers)

    alerts = run_full_detection(shipments, inventory, suppliers)
    result = generate_notifications(alerts)
    _notification_store["latest"] = result

    flash(f"Sample data analyzed — {result['total_alerts']} disruptions detected.", "success")
    return redirect(url_for("notifications"))


@app.route("/notifications")
def notifications():
    return render_template("notifications.html",
                           data=_notification_store.get("latest"),
                           use_genai=config.USE_GENAI)


@app.route("/api/notifications/json")
def notifications_json():
    data = _notification_store.get("latest")
    if data is None:
        return jsonify({"error": "No analysis results yet. Upload data or run sample analysis first."}), 404
    return jsonify(data)


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(os.path.join(data_dir, "shipments.csv")):
        print("Generating sample data...")
        save_sample_csv(data_dir)

    app.run(debug=True, host="0.0.0.0", port=5000)
