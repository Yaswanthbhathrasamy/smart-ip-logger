from flask import Flask, request, render_template, redirect
import os, json, uuid, requests, smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
DB_FILE = "url_db.json"

# Load or save URL mappings
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

# Fetch IP geolocation
def get_geolocation(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}")
        return res.json()
    except:
        return {}

# Email alert
def send_email_alert(ip_data, short_code):
    msg = EmailMessage()
    msg['Subject'] = f"[Visitor] Clicked on /track/{short_code}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL

    msg.set_content(f"""
🔍 New IP Visit
--------------------------
Short Code: {short_code}
IP: {ip_data.get('query', 'N/A')}
ISP: {ip_data.get('isp', 'N/A')}
City: {ip_data.get('city', 'N/A')}
Region: {ip_data.get('regionName', 'N/A')}
Country: {ip_data.get('country', 'N/A')}
Timezone: {ip_data.get('timezone', 'N/A')}
Coords: {ip_data.get('lat', 'N/A')} / {ip_data.get('lon', 'N/A')}
    """)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("[✔] Email sent.")
    except Exception as e:
        print("[✘] Email error:", e)

# Home - Enter URL
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get("url")
        short_code = uuid.uuid4().hex[:6]
        db = load_db()
        db[short_code] = url
        save_db(db)
        return render_template("index.html", short_url=f"http://127.0.0.1:5000/track/{short_code}")
    return render_template("index.html")

# Tracker
@app.route('/track/<code>')
def track(code):
    db = load_db()
    real_url = db.get(code)
    if not real_url:
        return "❌ Invalid link", 404

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    geo_data = get_geolocation(ip)
    send_email_alert(geo_data, code)
    return redirect(real_url)

if __name__ == "__main__":
    app.run(debug=True)
