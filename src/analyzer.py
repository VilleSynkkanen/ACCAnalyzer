import math
import csv
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
import numpy as np
import time
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def to_seconds(time):
    t = time.split(':')
    mins = float(t[0])
    secs = t[1].split(secs_delim)
    return mins*60+float(secs[0])+float(secs[1])/1000

def to_liters(fuel):
    f = fuel.strip('L').split(secs_delim)
    return float(f[0])+float(f[1])/10


filename = 'SGxVCOFinalsR2.csv'
driver = 'Ville Synkkanen (SYN)'
secs_delim = ','
remove_outliers = True
outlier_margin = 0.025
fit_degree = 2

r1 = None
laps = []
with open(filename, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        if r1 is None:
            r1 = row
        else:
            laps.append(row)

laptime_idx = r1.index('Lap Time')
lap_idx = r1.index('Lap')
driver_idx = r1.index('Driver')
tyreset_idx = r1.index('Tyre Set')
fuel_idx = r1.index('Fuel')

# 2D array with laps divided into stints
# Stint end is inferred from changed tyres or increased fuel
stints = []
times = []
fuel = math.inf
tyre_set = None
for l in laps:
    if l[driver_idx] == driver:
        if tyre_set is None:
            tyre_set = int(l[tyreset_idx])
        elif tyre_set != int(l[tyreset_idx]) or to_liters(l[fuel_idx]) > fuel:
            # Stint ended
            stints.append(times)
            times = []
        times.append(to_seconds(l[laptime_idx]))
        fuel = to_liters(l[fuel_idx])
        tyre_set = int(l[tyreset_idx])
stints.append(times)

# Plot lap times for each stint
story=[]
stint_idx = 1
for st in stints:
    #stint = s[1:len(s)-1]

    stint = []
    lap_nums = []
    ln = 1
    fastest = min(st)
    for lap in st:
        if lap < fastest*(1+outlier_margin):
            stint.append(lap)
            lap_nums.append(ln)
        ln += 1

    stint = np.array(stint)
    lap_nums = np.array(lap_nums)
    average = np.average(stint)
    plt.plot(lap_nums, stint, 'o')

    p = np.poly1d(np.polyfit(lap_nums, stint, fit_degree))
    plt.plot(lap_nums, p(lap_nums))
    plt.title("Stint " + str(stint_idx))
    plt.xlabel("Lap")
    plt.ylabel("Lap time")
    #plt.legend()

    plt.savefig("Stint" + str(stint_idx) + ".png", format="png", bbox_inches="tight", dpi=400)
    #plt.show()
    plt.clf()

    im = Image("Stint" + str(stint_idx) + ".png", 3 * inch, 3 * inch)
    story.append(im)
    story.append(Paragraph("Average laptime: " + str(average)))
    stint_idx += 1

# Create PDF
doc = SimpleDocTemplate("Analysis.pdf")
doc.build(story)