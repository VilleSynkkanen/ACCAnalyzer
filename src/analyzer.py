import math
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
import numpy as np
import time
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from utils import data_reader, to_seconds, to_liters, get_image, to_minutes_str

filename = 'SGxVCOFinalsR2.csv'
driver = 'Ville Synkkanen (SYN)'
data_dir = 'data'
img_dir = 'images'
out_dir = 'analysis'

outlier_margin = 0.025
fit_degree = 2
plot_dpi = 300

# Read CSV file
r1, laps = data_reader(data_dir, filename)

# Get column indexes for important data
laptime_idx = r1.index('Lap Time')
lap_idx = r1.index('Lap')
driver_idx = r1.index('Driver')
tyreset_idx = r1.index('Tyre Set')
fuel_idx = r1.index('Fuel')

# Divide laps into stints.
# Stints is a 2D array with laps as tuples (lap time, lap number) divided into stints.
# Stint end is inferred from changed tyres or increased fuel.
stints = []
times = []
fuel_stints = []
fuel_stints_end = []
fuel = math.inf
tyre_set = None
for l in laps:
    if l[driver_idx] == driver:
        if tyre_set is None:
            tyre_set = int(l[tyreset_idx])
        elif tyre_set != int(l[tyreset_idx]) or to_liters(l[fuel_idx]) > fuel:
            stints.append(times)
            fuel_stints.append(to_liters(laps[times[0][1]-1][fuel_idx]))
            fuel_stints_end.append(to_liters(laps[times[len(times) - 1][1]-1][fuel_idx]))
            times = []
        times.append((to_seconds(l[laptime_idx]), int(l[lap_idx])))
        fuel = to_liters(l[fuel_idx])
        tyre_set = int(l[tyreset_idx])
stints.append(times)
fuel_stints.append(to_liters(laps[times[0][1]-1][fuel_idx]))
fuel_stints_end.append(to_liters(laps[times[len(times) - 1][1]-1][fuel_idx]))

#print(fuel_stints)
#print(fuel_stints_end)

# Plot lap times for each stint
stint_idx = 1
avgs = []
excl_laps = []
# Remove outlier laps
for st in stints:
    ex = 0
    stint = []
    lap_nums = []
    fastest = min(st)[0]
    for lap in st:
        if lap[0] < fastest*(1+outlier_margin):
            stint.append(lap[0])
            lap_nums.append(lap[1])
        else:
            ex += 1

    # Add lap data into numpy arrays
    stint = np.array(stint)
    lap_nums = np.array(lap_nums)
    avgs.append(np.average(stint))
    excl_laps.append(ex)
    # Fit data into a curve and plot it
    # Plot a histogram into the same subplot
    f, (ax1, ax2) = plt.subplots(1, 2)
    f.set_figwidth(10)
    p = np.poly1d(np.polyfit(lap_nums, stint, fit_degree))
    counts, bins = np.histogram(stint)
    ax1.plot(lap_nums, stint, 'o')
    ax1.plot(lap_nums, p(lap_nums))
    ax2.stairs(counts, bins, fill=True)

    #plt.title("Stint " + str(stint_idx))
    #plt.xlabel("Lap")
    #plt.ylabel("Lap time")

    # Save and clear plot
    plt.savefig(img_dir + "/" + "Stint" + str(stint_idx) + ".png", format="png", bbox_inches="tight", dpi=plot_dpi)
    #plt.show()
    plt.clf()
    stint_idx += 1


# Create PDF
story = []
for i in range(len(stints)):
    story.append(Paragraph("Stint" + str(i + 1)))
    im = get_image(img_dir + "/" + "Stint" + str(i + 1) + ".png", width=16*cm)
    im.hAlign = 'CENTER'
    story.append(im)
    story.append(Paragraph("Average laptime: " + to_minutes_str(avgs[i])))
    story.append(Paragraph("Excluded laps: " + str(excl_laps[i])))
    story.append(Paragraph("Starting fuel: " + str(fuel_stints[i])))
    story.append(Paragraph("Fuel left: " + str(fuel_stints_end[i])))

doc = SimpleDocTemplate(out_dir + "/" + "Analysis.pdf")
doc.build(story)

