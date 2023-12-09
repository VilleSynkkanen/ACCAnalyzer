import math
import matplotlib.pyplot as plt
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table
from reportlab.lib.units import cm
from utils import data_reader, to_seconds, to_liters, get_image, to_minutes_str, condition_to_int, rain_to_int

filename = "SGxVCOFinalsR2"
driver_id = "SYN"
data_dir = 'data'
img_dir = 'images'
out_dir = 'analysis'

outlier_margin = 0.06
comparison_lap_count = 3
fit_degree = 2
plot_dpi = 300

# Read CSV file
r1, laps = data_reader(data_dir, filename + ".csv")

_, laps_f = data_reader(data_dir, filename + "_fixed.csv")
r1_f = laps_f[0]
laps_f = laps_f[1:]

# Get column indexes for important data
laptime_idx = r1.index('Lap Time')
lap_idx = r1.index('Lap')
driver_idx = r1.index("Driver")
driver_id_idx = r1.index("Short Name")
tyreset_idx = r1.index('Tyre Set')
fuel_idx = r1.index('Fuel')
accidents_idx = r1.index('Accidents')
conditions_idx = r1.index('Track Grip')
rain_idx = r1.index('Rain Intensity')
tyres_idx = r1.index('Tyres')
air_temp_idx = r1.index('Â° Air')
road_temp_idx = r1.index('Â° Road')

invalid_idx = r1_f.index('Penalty')

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
invalid_laps = []
invalid_stints = []
conditions = []
conditions_stint = []
rain = []
rain_stint = []
tyres = []
tyres_stint = []
air_temp = []
air_temp_stint = []
road_temp = []
road_temp_stint = []
accidents = []
accidents_cur = 0
fuel_stints = []
fuel_stints_end = []
fuel = math.inf
tyre_set = None
race_laps = len(laps)
track = laps[0][0]
car = laps[0][1]
drivers = []
for i in range(race_laps):
    if laps[i][driver_idx] not in drivers:
        drivers.append(laps[i][driver_idx])
    if laps[i][driver_id_idx].lower() == driver_id.lower():
        if tyre_set is None:
            tyre_set = int(laps[i][tyreset_idx])
        elif tyre_set != int(laps[i][tyreset_idx]) or to_liters(laps[i][fuel_idx]) > fuel:
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

            invalid_stints.append(invalid_laps)
            invalid_laps = []
            accidents.append(accidents_cur)
            accidents_cur = 0
            conditions.append(conditions_stint)
            conditions_stint = []
            rain.append(rain_stint)
            rain_stint = []
            tyres.append(tyres_stint)
            tyres_stint = []
            air_temp.append(air_temp_stint)
            air_temp_stint = []
            road_temp.append(road_temp_stint)
            road_temp_stint = []

        times.append((to_seconds(laps[i][laptime_idx]), int(laps[i][lap_idx])))
        times_s1.append((to_seconds(laps[i][sector1_idx]), int(laps[i][lap_idx])))
        times_s2.append((to_seconds(laps[i][sector2_idx]), int(laps[i][lap_idx])))
        times_s3.append((to_seconds(laps[i][sector3_idx]), int(laps[i][lap_idx])))

        fuel = to_liters(laps[i][fuel_idx])
        tyre_set = int(laps[i][tyreset_idx])
        if laps_f[i][invalid_idx] == "Invalid lap. ":
            invalid_laps.append(int(laps[i][lap_idx]))
        accidents_cur += int(laps[i][accidents_idx])
        conditions_stint.append(condition_to_int(laps[i][conditions_idx]))
        rain_stint.append(rain_to_int(laps[i][rain_idx]))
        tyres_stint.append(laps[i][tyres_idx])
        air_temp_stint.append(laps[i][air_temp_idx])
        road_temp_stint.append(laps[i][road_temp_idx])

stints.append(times)
stints_s1.append(times_s1)
stints_s2.append(times_s2)
stints_s3.append(times_s3)

fuel_stints.append(to_liters(laps[times[0][1]-1][fuel_idx]))
fuel_stints_end.append(to_liters(laps[times[len(times) - 1][1]-1][fuel_idx]))
invalid_stints.append(invalid_laps)
accidents.append(accidents_cur)
conditions.append(conditions_stint)
rain.append(rain_stint)
tyres.append(tyres_stint)
air_temp.append(air_temp_stint)
road_temp.append(road_temp_stint)

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
invalid_laps = []
# Remove outlier laps
for i in range(len(stints)):
    stint = []
    stint_s1 = []
    stint_s2 = []
    stint_s3 = []
    lap_nums = []
    lap_nums_all = []
    exc = []
    comparison_laps = [min(stints[i])[0]]
    total_laps.append(len(stints[i]))
    for j in range(len(stints[i])):
        lap_nums_all.append(stints[i][j][1])
        if not (j == 0 or (j == len(stints[i]) - 1 and j != race_laps - 1)) \
                and stints[i][j][0] < sum(comparison_laps)/len(comparison_laps)*(1 + outlier_margin):
            stint.append(stints[i][j][0])
            stint_s1.append(stints_s1[i][j][0])
            stint_s2.append(stints_s2[i][j][0])
            stint_s3.append(stints_s3[i][j][0])
            lap_nums.append(stints[i][j][1])
            comparison_laps.append(stints[i][j][0])
            if len(comparison_laps) > comparison_lap_count:
                comparison_laps = comparison_laps[1:]
        else:
            exc.append(stints[i][j][1])

    # Add lap data into numpy arrays
    stint = np.array(stint)
    stint_s1 = np.array(stint_s1)
    stint_s2 = np.array(stint_s2)
    stint_s3 = np.array(stint_s3)
    lap_nums = np.array(lap_nums)
    lap_nums_all = np.array(lap_nums_all)


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

    # Conditions plotting
    f, (ax1, ax2, ax3) = plt.subplots(3, 1)
    f.set_figwidth(5)
    ax1.plot(lap_nums_all, conditions[i])
    ax2.plot(lap_nums_all, rain[i])
    ax3.plot(lap_nums_all, air_temp[i])
    ax3.plot(lap_nums_all, road_temp[i], '-')

    plt.savefig(img_dir + "/" + filename + "_stint" + str(stint_idx) + "conditions.png", format="png", bbox_inches="tight",
                dpi=plot_dpi)

    stint_idx += 1

# Create PDF
story = []
story.append(Paragraph(filename + " Analysis"))
story.append(Paragraph("Car: " + car))
story.append(Paragraph("Track: " + track))
story.append(Paragraph("Race laps: " + str(race_laps)))
drivers_p = ""
if len(drivers) > 1:
    drivers_p += "Drivers: "
else:
    drivers_p += "Driver: "
for dr in drivers:
    drivers_p += dr + ", "
story.append(Paragraph(drivers_p))
for i in range(len(stints)):

    story.append(Paragraph("Stint" + str(i + 1)))

    im = get_image(img_dir + "/" + filename + "_stint" + str(i + 1) + ".png", width=15*cm)
    im.hAlign = 'CENTER'
    story.append(im)

    im = get_image(img_dir + "/" + filename + "_stint" + str(i + 1) + "sectors.png", width=15 * cm)
    im.hAlign = 'CENTER'
    story.append(im)

    im = get_image(img_dir + "/" + filename + "_stint" + str(i + 1) + "conditions.png", width=7 * cm)
    im.hAlign = 'LEFT'


    p = ""
    p += "Average laptime: " + to_minutes_str(avgs[i]) + "\n"
    p += "Laptime standard deviation: " + to_minutes_str(stds[i]) + "\n"

    p += "Average sector times: " + to_minutes_str(avgs_s1[i]) + " " + to_minutes_str(avgs_s2[i]) + " " \
         + to_minutes_str(avgs_s3[i]) + "\n"
    p += "Sector times standard deviation: " + to_minutes_str(stds_s1[i]) + " " \
         + to_minutes_str(stds_s2[i]) + " " + to_minutes_str(stds_s3[i])  + "\n"
    p += "Total laps: " + str(total_laps[i]) + "\n"
    p += "Invalid laps: " + str(len(invalid_stints[i])) + " (" + \
         str(((len(invalid_stints[i])/total_laps[i])*100).__round__(1)) + "%)" + "\n"
    excluded_str = "Excluded laps: "
    for ex in excl_laps[i]:
        excluded_str += str(ex) + " "
    p += excluded_str + "\n"
    p += "Incidents: " + str(accidents[i]) + "\n"
    p += "Starting fuel: " + str(fuel_stints[i]) + "\n"
    p += "Fuel left: " + str(fuel_stints_end[i]) + "\n"
    p += "Tyres used: " + tyres[i][0] + "\n"

    data = [[im, p]]
    t = Table(data)
    story.append(t)

    story.append(PageBreak())

doc = SimpleDocTemplate(out_dir + "/" + filename + "_analysis.pdf")
doc.build(story)

