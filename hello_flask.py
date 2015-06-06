# sudo gunicorn hello_flask:app -p rocket.pid -b 192.168.1.151:80 -D
from flask import Flask
app = Flask(__name__)

print (app)

@app.route("/")
def index():
    return "Hello World!"

