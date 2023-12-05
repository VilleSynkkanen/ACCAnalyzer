import math
import matplotlib.pyplot as plt
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.units import inch, cm
from utils import data_reader, to_seconds, to_liters, get_image, to_minutes_str

filename = "MozaChallengeS4R3"
driver_id = "SYN"
data_dir = 'data'
img_dir = 'images'
out_dir = 'analysis'

outlier_margin = 0.025
fit_degree = 2
plot_dpi = 300

# Read CSV file
r1, laps = data_reader(data_dir, filename + ".csv")

# Get column indexes for important data
laptime_idx = r1.index('Lap Time')
lap_idx = r1.index('Lap')
driver_id_idx = r1.index("Short Name")
tyreset_idx = r1.index('Tyre Set')
fuel_idx = r1.index('Fuel')
accidents_idx = r1.index('Accidents')

sector1_idx = r1.index('Sector 1')
sector2_idx = r1.index('Sector 2')
sector3_idx = r1.index('Sector 3')

# Divide laps into stints.
# Stints is a 2D array with laps as tuples (lap time, lap number) divided into stints.
# Stint end is inferred from changed tyres or increased fuel.
stints = []
times = []
stints_s1 = []
times_s1 = []
stints_s2 = []
times_s2 = []
stints_s3 = []
times_s3 = []
fuel_stints = []
fuel_stints_end = []
fuel = math.inf
tyre_set = None
for l in laps:
    if l[driver_id_idx].lower() == driver_id.lower():
        if tyre_set is None:
            tyre_set = int(l[tyreset_idx])
        elif tyre_set != int(l[tyreset_idx]) or to_liters(l[fuel_idx]) > fuel:
            stints.append(times)
            stints_s1.append(times_s1)
            stints_s2.append(times_s2)
            stints_s3.append(times_s3)

            fuel_stints.append(to_liters(laps[times[0][1]-1][fuel_idx]))
            fuel_stints_end.append(to_liters(laps[times[len(times) - 1][1]-1][fuel_idx]))
            times = []
            times_s1 = []
            times_s2 = []
            times_s3 = []

        times.append((to_seconds(l[laptime_idx]), int(l[lap_idx])))
        times_s1.append((to_seconds(l[sector1_idx]), int(l[lap_idx])))
        times_s2.append((to_seconds(l[sector2_idx]), int(l[lap_idx])))
        times_s3.append((to_seconds(l[sector3_idx]), int(l[lap_idx])))

        fuel = to_liters(l[fuel_idx])
        tyre_set = int(l[tyreset_idx])

stints.append(times)
stints_s1.append(times_s1)
stints_s2.append(times_s2)
stints_s3.append(times_s3)

fuel_stints.append(to_liters(laps[times[0][1]-1][fuel_idx]))
fuel_stints_end.append(to_liters(laps[times[len(times) - 1][1]-1][fuel_idx]))

# Plot lap times for each stint
stint_idx = 1
avgs = []
stds = []

avgs_s1 = []
stds_s1 = []
avgs_s2 = []
stds_s2 = []
avgs_s3 = []
stds_s3 = []

excl_laps = []
total_laps = []
# Remove outlier laps
for i in range(len(stints)):
    stint = []
    stint_s1 = []
    stint_s2 = []
    stint_s3 = []
    lap_nums = []
    exc = []
    fastest = min(stints[i])[0]
    total_laps.append(len(stints[i]))
    for j in range(len(stints[i])):
        if stints[i][j][0] < fastest*(1+outlier_margin):
            stint.append(stints[i][j][0])
            stint_s1.append(stints_s1[i][j][0])
            stint_s2.append(stints_s2[i][j][0])
            stint_s3.append(stints_s3[i][j][0])
            lap_nums.append(stints[i][j][1])
        else:
            exc.append(stints[i][j][1])


    # Add lap data into numpy arrays
    stint = np.array(stint)
    stint_s1 = np.array(stint_s1)
    stint_s2 = np.array(stint_s2)
    stint_s3 = np.array(stint_s3)
    lap_nums = np.array(lap_nums)

    #print(stint_s1)
    #print(stint_s2)
    #print(stint_s3)
    #print(lap_nums)

    avgs.append(np.average(stint))
    stds.append(np.std(stint))

    avgs_s1.append(np.average(stint_s1))
    stds_s1.append(np.std(stint_s1))
    avgs_s2.append(np.average(stint_s2))
    stds_s2.append(np.std(stint_s2))
    avgs_s3.append(np.average(stint_s3))
    stds_s3.append(np.std(stint_s3))
    excl_laps.append(exc)
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
    plt.savefig(img_dir + "/" + filename + "_stint" + str(stint_idx) + ".png", format="png", bbox_inches="tight", dpi=plot_dpi)
    #plt.show()
    plt.clf()

    # Sector time plotting
    f, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3)
    f.set_figwidth(10)
    sectors = [stint_s1, stint_s2, stint_s3]
    axes = [ax1, ax2, ax3, ax4, ax5, ax6]
    for s in range(3):
        p = np.poly1d(np.polyfit(lap_nums, sectors[s], fit_degree))
        counts, bins = np.histogram(sectors[s])
        axes[s].plot(lap_nums, sectors[s], 'o')
        axes[s].plot(lap_nums, p(lap_nums))
        axes[s+3].stairs(counts, bins, fill=True)

    plt.savefig(img_dir + "/" + filename + "_stint" + str(stint_idx) + "sectors.png", format="png", bbox_inches="tight", dpi=plot_dpi)
    #plt.show()
    stint_idx += 1

# Create PDF
story = []
for i in range(len(stints)):
    story.append(Paragraph("Stint" + str(i + 1)))

    im = get_image(img_dir + "/" + filename + "_stint" + str(i + 1) + ".png", width=16*cm)
    im.hAlign = 'CENTER'
    story.append(im)

    im = get_image(img_dir + "/" + filename + "_stint" + str(i + 1) + "sectors.png", width=16 * cm)
    im.hAlign = 'CENTER'
    story.append(im)

    story.append(Paragraph("Average laptime: " + to_minutes_str(avgs[i])))
    story.append(Paragraph("Laptime standard deviation: " + to_minutes_str(stds[i])))

    story.append(Paragraph("Average sector times: " + to_minutes_str(avgs_s1[i]) + " "
                           + to_minutes_str(avgs_s2[i]) + " " + to_minutes_str(avgs_s3[i])))
    story.append(Paragraph("Sector times standard deviation: " + to_minutes_str(stds_s1[i]) + " "
                           + to_minutes_str(stds_s2[i]) + " " + to_minutes_str(stds_s3[i])))
    story.append(Paragraph("Total laps: " + str(total_laps[i])))
    excluded_str = "Excluded laps: "
    for ex in excl_laps[i]:
        excluded_str += str(ex) + " "
    story.append(Paragraph(excluded_str))
    story.append(Paragraph("Starting fuel: " + str(fuel_stints[i])))
    story.append(Paragraph("Fuel left: " + str(fuel_stints_end[i])))
    story.append(PageBreak())

doc = SimpleDocTemplate(out_dir + "/" + filename + "_analysis.pdf")
doc.build(story)

