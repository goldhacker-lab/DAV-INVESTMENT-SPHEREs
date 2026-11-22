
from flask import Flask, jsonify, send_file
import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone

app = Flask(__name__)

RBI_URL = "https://www.rbi.org.in/"

def get_rbi_data():
    response = requests.get(
        RBI_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

    def find_rate(label):
        pattern = re.escape(label) + r"\s*[:|]\s*([0-9]+(?:\.[0-9]+)?)\s*%"
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    def find_number(label):
        pattern = re.escape(label) + r"\s*[:|]\s*([0-9]+(?:\.[0-9]+)?)"
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    rates = {
        "repo": find_rate("Policy Repo Rate"),
        "sdf": find_rate("Standing Deposit Facility Rate"),
        "msf": find_rate("Marginal Standing Facility Rate"),
        "bank_rate": find_rate("Bank Rate"),
        "reverse_repo": find_rate("Fixed Reverse Repo Rate"),
        "crr": find_rate("CRR"),
        "slr": find_rate("SLR"),
        "usd_inr": find_number("INR / 1 USD"),
        "gbp_inr": find_number("INR / 1 GBP"),
        "eur_inr": find_number("INR / 1 EUR"),
    }

    if all(value is None for value in rates.values()):
        raise ValueError("Could not identify RBI rates on the page.")

    date_match = re.search(
        r"As at\s+(.{0,80}?)(?=\s+Lending|\s+Market|\s+Source|$)",
        text,
        re.IGNORECASE
    )

    return {
        "success": True,
        "source": "Reserve Bank of India",
        "source_url": RBI_URL,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "observation_date": date_match.group(1) if date_match else "See RBI website",
        "rates": rates
    }


@app.route("/")
def home():
    html_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "index.html"
    )
    return send_file(html_path)


@app.route("/api/rbi/current-rates")
def current_rates():
    try:
        return jsonify(get_rbi_data())
    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
            "source_url": RBI_URL
        }), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
