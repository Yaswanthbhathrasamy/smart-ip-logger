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


def send_email_alert(ip_data, short_code, recipient_email):
    msg = EmailMessage()
    msg['Subject'] = f"[Visitor] Tracked /track/{short_code}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email

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
        recipient_email = request.form.get("to_email")

        if not url.startswith("http"):
            url = "http://" + url

        short_code = uuid.uuid4().hex[:6]
        db = load_db()
        db[short_code] = {"url": url, "email": recipient_email}
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
    recipient_email = entry["email"]

    ip_header = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip_header.split(",")[0].strip() if "," in ip_header else ip_header

    geo_data = get_geolocation(ip)
    geo_data["query"] = ip  

    send_email_alert(geo_data, code, recipient_email)

    return redirect(real_url)



if __name__ == "__main__":
    app.run(debug=True)

