from flask import Flask, request, render_template, redirect
import os, json, uuid, requests, smtplib
from email.message import EmailMessage

app = Flask(__name__)


EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
DB_FILE = "url_db.json"


def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)


def get_geolocation(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}")
        return res.json()
    except Exception as e:
        print("[Geo Error]:", e)
        return {}


def send_email_alert(ip_data, short_code):
    msg = EmailMessage()
    msg['Subject'] = f"[Visitor] Tracked /track/{short_code}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL

    msg.set_content(f"""
New Visitor Alert

Short Code: {short_code}
IP Address: {ip_data.get('query', 'N/A')}
ISP: {ip_data.get('isp', 'N/A')}
City: {ip_data.get('city', 'N/A')}
Region: {ip_data.get('regionName', 'N/A')}
Country: {ip_data.get('country', 'N/A')}
Timezone: {ip_data.get('timezone', 'N/A')}
Coordinates: {ip_data.get('lat', 'N/A')} / {ip_data.get('lon', 'N/A')}
""")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("[✔] Email sent successfully.")
    except Exception as e:
        print("[✘] Email send failed:", e)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get("url")
        if not url.startswith("http"):
            url = "http://" + url

        short_code = uuid.uuid4().hex[:6]
        db = load_db()
        db[short_code] = url
        save_db(db)

        short_url = request.host_url + "track/" + short_code
        return render_template("index.html", short_url=short_url)

    return render_template("index.html")


@app.route('/track/<code>')
def track(code):
    db = load_db()
    real_url = db.get(code)
    if not real_url:
        return "Invalid or expired link.", 404

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    geo_data = get_geolocation(ip)
    send_email_alert(geo_data, code)
    return redirect(real_url)

if __name__ == "__main__":
    app.run(debug=True)
