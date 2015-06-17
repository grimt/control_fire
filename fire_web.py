# Flask web interface app for fire controller

# sudo gunicorn fire_web:app -p fire_web.pid -b 192.168.1.151:80 -D
# sudo gunicorn fire_web:app -b 192.168.1.151:80 

from flask import Flask, render_template
import datetime

def write_desired_temp_to_file (temp):

    try:
        f = open ('/tmp/temperature.txt','wt')
        f.write (str (temp))
        f.close ()
    except IOError:
        print ('Could not write desired temperature to a file')


def read_desired_temp_from_file():
    temp = 0
    try:
        f = open ('/tmp/temperature.txt','rt')
        temp = f.read ()
        f.close ()
    except IOError:
        temp = 0
    return temp
    
def read_measured_temp_from_file ():
    temp = 0 
    try:
        f = open ('/tmp/measured_temperature.txt','rt')
        temp = f.read ()
        f.close ()
    except IOError:
                temp = 0
    return temp

def read_fire_status_from_file ():
    try:
        f = open ('/tmp/fire_status.txt', 'rt')
        status = f.read ()
        f.close ()
    except IOError:
        status = 'Error'
    return status

def update_desired_temp (temp):
    write_desired_temp_to_file (temp)

def read_measured_temp():
    return read_measured_temp_from_file()
    
def read_desired_temp():
    return (read_desired_temp_from_file ())

def read_fire_status():
    return read_fire_status_from_file ()

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
    status = read_fire_status()
    dtemp = read_desired_temp()
    mtemp = read_measured_temp()
    templateData = {
        'title' : 'Fire!',
        'status': status,
        'dtemp': str(dtemp),
        'mtemp': str(mtemp)
        }
    print('Here 1')
    return render_template('main.html', **templateData)
          
@app.route("/submit/<int:temp>")
def submit (temp):
    status = read_fire_status()
    update_desired_temp (temp)
    mtemp = read_measured_temp()
    templateData = {
        'title' : 'Fire!',
        'status' : status,
        'dtemp': str(temp),
        'mtemp': str(mtemp)
        }
    return render_template('main.html', **templateData)
    
#if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=80, debug=True)
