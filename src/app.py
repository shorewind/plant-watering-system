from flask import Flask, render_template
import main # runs main.py
# Setup web server
app = Flask(__name__)

time = []
moisture = []
temperature = []
humidity = []

file = open("plant_data.txt", "r")
lines = file.readlines()

iteration = 0
for line in lines:
    iteration += 1
    time.append(iteration)
    line = line.strip().split(', ')
    moisture.append(float(line[0]))
    temperature.append(float(line[1]))
    humidity.append(float(line[2]))

@app.route("/")
def graphs():
    return render_template("index.html", time = time, moist_values = moisture, temp_values = temperature, humid_values = humidity)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
