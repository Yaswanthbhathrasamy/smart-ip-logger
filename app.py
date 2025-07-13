from flask import Flask, request, render_template, redirect
import os, json, uuid, requests, smtplib
from email.message import EmailMessage

app = Flask(__name__)

DB_FILE = "url_db.json"
EMAIL_ADDRESS = "yaswanthyaswsnth@gmail.com"
EMAIL_PASSWORD = "izpgmmarafnznuoe"

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

def send_email_alert(ip_data_list, short_code, to_email):
    msg = EmailMessage()
    msg['Subject'] = f"[Visitor] Tracked /track/{short_code}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    content = f"New Visitor Alert\n\nShort Code: {short_code}\n\n"

    for idx, data in enumerate(ip_data_list):
        content += f"IP #{idx + 1}: {data.get('query', 'N/A')}\n"
        content += f"  ISP: {data.get('isp', 'N/A')}\n"
        content += f"  City: {data.get('city', 'N/A')}\n"
        content += f"  Region: {data.get('regionName', 'N/A')}\n"
        content += f"  Country: {data.get('country', 'N/A')}\n"
        content += f"  Timezone: {data.get('timezone', 'N/A')}\n"
        content += f"  Coordinates: {data.get('lat', 'N/A')} / {data.get('lon', 'N/A')}\n\n"

    msg.set_content(content)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            print("[✔] Email sent successfully.")
    except Exception as e:
        print("[✘] Email send failed:", e)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get("url")
        to_email = request.form.get("to_email")
        if not url.startswith("http"):
            url = "http://" + url

        short_code = uuid.uuid4().hex[:6]
        db = load_db()
        db[short_code] = {"url": url, "email": to_email}
        save_db(db)

        short_url = request.host_url + "track/" + short_code
        return render_template("index.html", short_url=short_url)

    return render_template("index.html")

@app.route('/track/<code>')
def track(code):
    db = load_db()
    entry = db.get(code)
    if not entry:
        return "Invalid or expired link.", 404

    real_url = entry["url"]
    to_email = entry["email"]

    ip_header = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip_list = [ip.strip() for ip in ip_header.split(",")]

    geo_data_list = []
    for ip in ip_list:
        geo = get_geolocation(ip)
        geo['query'] = ip
        geo_data_list.append(geo)

    send_email_alert(geo_data_list, code, to_email)
    return redirect(real_url)

if __name__ == "__main__":
    app.run(debug=True)
