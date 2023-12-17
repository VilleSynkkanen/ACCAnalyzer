import math
import os
import matplotlib.pyplot as plt
import numpy as np
from configparser import ConfigParser
from pathlib import Path
from matplotlib import ticker
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, Spacer, TableStyle
from reportlab.lib.units import cm
from utils import data_reader, to_seconds, to_liters, get_image, to_minutes_str, condition_to_int, rain_to_int, \
    gap_to_float, get_track_map, secs_to_mins, condition_ticks, rain_ticks, temps_to_float, fix_missing_sectors

track_dir = 'resources/tracks'
car_dir = 'resources/cars'
out_img_dir = 'resources/temp'
settings_dir = 'config'

# Read ini file
config = ConfigParser()
config.read(settings_dir + '/' + 'settings.ini', encoding='utf-8')

try:
    driver = config.get('SETTINGS', 'driver')
    outlier_margin = float(config.get('SETTINGS', 'outlier_margin'))
    comparison_lap_count = int(config.get('SETTINGS', 'comparison_lap_count'))
    comparison_lap_add_margin = float(config.get('SETTINGS', 'comparison_lap_add_margin'))
    fit_degree = int(config.get('SETTINGS', 'fit_degree'))
    plot_dpi = int(config.get('SETTINGS', 'plot_dpi'))
    data_dir = os.path.normcase(config.get('SETTINGS', 'data_dir'))
    out_dir = os.path.normcase(config.get('SETTINGS', 'out_dir'))
except ValueError:
    print("Invalid settings.")
    exit()

close = False
while not close:
    filename = input("Data file name (without .csv) or press Enter to exit: ")
    if filename == "":
        close = True
        continue
    # Read CSV file
    try:
        r1, laps = data_reader(data_dir, filename + ".csv")
        _, laps_f = data_reader(data_dir, filename + "_fixed.csv")
        r1_f = laps_f[0]
        laps_f = laps_f[1:]
    except FileNotFoundError:
        print("Data files not found.")
        continue

    analysis_title = input("Title of the analysis: ")
    additional_params = input("Additional settings: ")

    """
    Possible additional parameters (overrides defaults:
    Outlier margin: om=...
    Fit degree: fd=...
    Skip race analysis: sr
    Laps to analyze: lta=..
    Use comma to split, e.g. om=0.01,fd=3,lta=3-27;71-89
    """
    om_changed = False
    fd_changed = False
    skip_race_analysis = False
    analyze_all_laps = True
    laps_to_analyze = []
    params = additional_params.rstrip().split(",")
    for par in params:
        par_spl = par.split("=")
        if par_spl[0] == "om":
            outlier_margin = float(par_spl[1])
            om_changed = True
        elif par_spl[0] == "fd":
            fit_degree = int(par_spl[1])
            fd_changed = True
        elif par_spl[0] == "sr":
            skip_race_analysis = True
        elif par_spl[0] == "lta":
            analyze_all_laps = False
            intervals = par_spl[1].split(";")
            for i in intervals:
                print(i)
                lps = i.split("-")
                for l in range(int(lps[0]), int(lps[1]) + 1):
                    laps_to_analyze.append(l)

    if om_changed:
        print("Using outlier margin " + str(outlier_margin))
    if fd_changed:
        print("Using fit degree " + str(fit_degree))
    if skip_race_analysis:
        print("Skipping race analysis")
    if not analyze_all_laps:
        print("Analyzing only specific laps")
    driver_names = driver.rstrip().lower().split(",")

    try:
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
        air_temp_idx = r1.index('° Air')
        road_temp_idx = r1.index('° Road')
        position_idx = r1.index('Position')
        gap_idx = r1.index('Gap')

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
        prev_lap = 0
        track = laps[0][0]
        car = laps[0][1]
        drivers = []
        position = []
        gap_ahead = []
        laps_all_drivers = []
        for i in range(race_laps):
            if int(laps[i][lap_idx]) not in laps_to_analyze and not analyze_all_laps:
                continue
            position.append(int(laps[i][position_idx]))
            gap_ahead.append(gap_to_float(laps[i][gap_idx]))
            laps_all_drivers.append((laps[i][driver_idx], int(laps[i][lap_idx])))
            if laps[i][driver_idx] not in drivers:
                drivers.append(laps[i][driver_idx])
            if laps[i][driver_idx].lower() in driver_names:
                if tyre_set is None:
                    tyre_set = int(laps[i][tyreset_idx])
                elif tyre_set != int(laps[i][tyreset_idx]) or to_liters(laps[i][fuel_idx]) > fuel \
                        or (prev_lap + 1 != int(laps[i][lap_idx])):
                    if len(times) > 1:
                        stints.append(times)
                        stints_s1.append(times_s1)
                        stints_s2.append(times_s2)
                        stints_s3.append(times_s3)

                        fuel_stints.append(to_liters(laps[times[0][1] - 1][fuel_idx]))
                        fuel_stints_end.append(to_liters(laps[times[len(times) - 1][1] - 1][fuel_idx]))
                        invalid_stints.append(invalid_laps)

                        accidents.append(accidents_cur)
                        conditions.append(conditions_stint)
                        rain.append(rain_stint)
                        tyres.append(tyres_stint)
                        air_temp.append(air_temp_stint)
                        road_temp.append(road_temp_stint)

                    accidents_cur = 0
                    times = []
                    times_s1 = []
                    times_s2 = []
                    times_s3 = []
                    invalid_laps = []
                    conditions_stint = []
                    rain_stint = []
                    tyres_stint = []
                    air_temp_stint = []
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
            prev_lap = int(laps[i][lap_idx])
        stints_all_drivers = []
        curr_driver = laps_all_drivers[0][0]
        curr_stint = []
        for lp in laps_all_drivers:
            if lp[0] == curr_driver:
                curr_stint.append(lp)
            else:
                stints_all_drivers.append(curr_stint)
                curr_stint = []
                curr_driver = lp[0]
                curr_stint.append(lp)

        stints_all_drivers.append(curr_stint)

        stint_start_end_all = []
        for st in stints_all_drivers:
            stint_start_end_all.append((st[0][0], st[0][1], st[-1][1]))

        stint_start_end_all = sorted(stint_start_end_all, key=lambda x: x[0])

        stints.append(times)
        stints_s1.append(times_s1)
        stints_s2.append(times_s2)
        stints_s3.append(times_s3)

        fuel_stints.append(to_liters(laps[times[0][1] - 1][fuel_idx]))
        fuel_stints_end.append(to_liters(laps[times[len(times) - 1][1] - 1][fuel_idx]))
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
        stint_start_end = []
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
            stint_start_end.append((stints[i][0], stints[i][-1]))
            for j in range(len(stints[i])):
                lap_nums_all.append(stints[i][j][1])
                # add comparison laps to a list
                new_comparison_laps = []
                for cl in range(j - comparison_lap_count, j + comparison_lap_count + 1):
                    if 0 <= cl < len(stints[i]):
                        # use lap for comparison if it's close enough to the previous comparison laps
                        if stints[i][cl][0] < sum(comparison_laps) / len(comparison_laps) * (
                                1 + comparison_lap_add_margin):
                            new_comparison_laps.append(stints[i][cl][0])
                if stints[i][j][0] < sum(new_comparison_laps) / len(new_comparison_laps) * (1 + outlier_margin) \
                        and j != 0 and (j != len(stints[i]) - 1 or j == race_laps - 1):
                    stint.append(stints[i][j][0])
                    stint_s1.append(stints_s1[i][j][0])
                    stint_s2.append(stints_s2[i][j][0])
                    stint_s3.append(stints_s3[i][j][0])
                    lap_nums.append(stints[i][j][1])
                else:
                    exc.append(stints[i][j][1])
                comparison_laps = new_comparison_laps

            stint_s1, stint_s2, stint_s3 = fix_missing_sectors(stint, stint_s1, stint_s2, stint_s3)

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
            f.suptitle('Lap times')
            ax1.set_xlabel('lap')
            ax1.set_yticks(ax1.get_yticks())
            ax1.set_yticklabels(secs_to_mins(ax1.get_yticks()))
            ax1.set_ylabel('time')
            ax2.set_xlabel('time')
            ax2.set_xticks(ax2.get_xticks())
            if len(ax2.get_xticks()) > 8:
                ax2.set_xticklabels(secs_to_mins(ax2.get_xticks()), fontsize=72 / len(ax2.get_xticks()))
            else:
                ax2.set_xticklabels(secs_to_mins(ax2.get_xticks()))
            ax2.set_ylabel('number of laps')
            ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

            # Save and clear plot
            plt.savefig(out_img_dir + "/" + filename + "_stint" + str(stint_idx) + ".png", format="png",
                        bbox_inches="tight", dpi=plot_dpi)
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
                axes[s + 3].stairs(counts, bins, fill=True)
                axes[s].set_title('Sector ' + str(s + 1) + ' times')
                axes[s].set_xlabel('lap')
                axes[s].set_yticks(axes[s].get_yticks())
                axes[s].set_yticklabels(secs_to_mins(axes[s].get_yticks()))
                axes[s].set_ylabel('time')
                axes[s + 3].set_xlabel('time')
                axes[s + 3].set_xticks(axes[s + 3].get_xticks())
                axes[s + 3].set_xticklabels(secs_to_mins(axes[s + 3].get_xticks()))
                axes[s + 3].set_ylabel('number of sectors')
                axes[s + 3].yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
                plt.tight_layout()

            plt.savefig(out_img_dir + "/" + filename + "_stint" + str(stint_idx) + "sectors.png", format="png",
                        bbox_inches="tight", dpi=plot_dpi)

            # Conditions plotting
            f, (ax1, ax2, ax3) = plt.subplots(3, 1)
            f.set_figwidth(5)
            ax1.plot(lap_nums_all, conditions[i])
            ax1.set_title("Track grip")
            ax1.set_yticks(ax1.get_yticks())
            ax1.set_yticklabels(condition_ticks(ax1.get_yticks()))
            ax2.plot(lap_nums_all, rain[i])
            ax2.set_title("Rain level")
            ax2.set_yticks(ax2.get_yticks())
            ax2.set_yticklabels(rain_ticks(ax2.get_yticks()))

            ax3.plot(lap_nums_all, temps_to_float(air_temp[i]))
            ax3.plot(lap_nums_all, temps_to_float(road_temp[i]), '-')
            ax3.set_title("Temperatures")
            ax3.set_ylabel("°C")
            ax3.set_xlabel('lap')
            ax3.legend(['ambient', 'road'])
            ax3.yaxis.set_major_locator(plt.MaxNLocator(4))
            plt.tight_layout()

            plt.savefig(out_img_dir + "/" + filename + "_stint" + str(stint_idx) + "conditions.png", format="png",
                        bbox_inches="tight", dpi=plot_dpi)

            stint_idx += 1

        # Race analysis
        f, (ax1, ax2) = plt.subplots(1, 2)
        f.set_figwidth(10)
        ax1.plot(position)
        ax1.set_title('Race position')
        ax1.set_xlabel('lap')
        ax1.set_ylabel('position')
        ax2.plot(gap_ahead)
        ax2.set_title('Gap to car ahead')
        ax2.set_xlabel('lap')
        ax2.set_ylabel('time (s)')

        plt.savefig(out_img_dir + "/" + filename + "position.png", format="png", bbox_inches="tight",
                    dpi=plot_dpi)

        # Create styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Heading_CENTER',
                                  parent=styles['Heading1'],
                                  fontName='Helvetica',
                                  wordWrap='LTR',
                                  alignment=TA_CENTER,
                                  fontSize=16,
                                  leading=13,
                                  textColor=colors.black,
                                  borderPadding=0,
                                  leftIndent=0,
                                  rightIndent=0,
                                  spaceAfter=0,
                                  spaceBefore=0,
                                  splitLongWords=True,
                                  spaceShrinkage=0.05,
                                  ))

        styles.add(ParagraphStyle(name='Heading2_LEFT',
                                  parent=styles['Heading2'],
                                  fontName='Helvetica',
                                  wordWrap='LTR',
                                  alignment=TA_LEFT,
                                  fontSize=13,
                                  leading=13,
                                  textColor=colors.black,
                                  borderPadding=0,
                                  leftIndent=0,
                                  rightIndent=0,
                                  spaceAfter=0,
                                  spaceBefore=0,
                                  splitLongWords=True,
                                  spaceShrinkage=0.05,
                                  ))

        styleHC = styles['Heading_CENTER']
        styleHL2 = styles['Heading2_LEFT']

        # Create PDF
        story = list()
        story.append(Paragraph(analysis_title + " Analysis", styleHC))
        story.append(Spacer(1, 24))
        story.append(Paragraph("General Information", styleHL2))
        story.append(Spacer(1, 6))
        drivers_p = ""
        if len(drivers) > 1:
            drivers_p += "Drivers: "
        else:
            drivers_p += "Driver: "
        for dr in drivers:
            drivers_p += dr + ", "
        drivers_p = drivers_p[:-2]
        story.append(Paragraph(drivers_p))
        story.append(Paragraph("Car: " + car))
        story.append(Paragraph("Track: " + track))

        im1 = get_track_map(track_dir, track, 7.5 * cm)
        im2 = get_image(car_dir + "/" + car + ".png", 7.5 * cm)
        data = [[im2, im1]]
        t = Table(data)
        t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        t.hAlign = 'CENTER'
        story.append(t)
        story.append(Spacer(1, 12))

        if not skip_race_analysis:
            story.append(Paragraph("Race Analysis", styleHL2))
            story.append(Spacer(1, 6))
            im = get_image(out_img_dir + "/" + filename + "position.png", width=15 * cm)
            im.hAlign = 'CENTER'
            story.append(im)
            story.append(Spacer(1, 6))
            drivers_table_p = ['Driver']
            laps_table_p = ['Laps driven']
            for dr in drivers:
                drivers_table_p.append(Paragraph(dr))
                laps_table_p_add = ""
                for st in stint_start_end_all:
                    if dr == st[0]:
                        laps_table_p_add += str(st[1]) + " - " + str(st[2]) + ", "
                laps_table_p_add = laps_table_p_add[:-2]
                laps_table_p.append(Paragraph(laps_table_p_add))
            data = [drivers_table_p, laps_table_p]
            t = Table(data)

            t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                                   ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
            story.append(t)
        story.append(PageBreak())

        for i in range(len(stints)):
            story.append(Paragraph("Stint " + str(i + 1) + " Analysis", styleHL2))
            story.append(Spacer(1, 6))

            im = get_image(out_img_dir + "/" + filename + "_stint" + str(i + 1) + ".png", width=16 * cm)
            im.hAlign = 'CENTER'
            story.append(im)

            im = get_image(out_img_dir + "/" + filename + "_stint" + str(i + 1) + "sectors.png", width=16 * cm)
            im.hAlign = 'CENTER'
            story.append(im)

            im = get_image(out_img_dir + "/" + filename + "_stint" + str(i + 1) + "conditions.png", width=6.8 * cm)
            im.hAlign = 'LEFT'

            lps = Paragraph(str(stint_start_end[i][0][1]) + " - " + str(stint_start_end[i][1][1]))
            avgl = Paragraph(to_minutes_str(avgs[i]))
            stdl = Paragraph(to_minutes_str(stds[i]))
            avg_s1 = Paragraph(to_minutes_str(avgs_s1[i], round_to=2))
            avg_s2 = Paragraph(to_minutes_str(avgs_s2[i], round_to=2))
            avg_s3 = Paragraph(to_minutes_str(avgs_s3[i], round_to=2))
            std_s1 = Paragraph(to_minutes_str(stds_s1[i], round_to=2))
            std_s2 = Paragraph(to_minutes_str(stds_s2[i], round_to=2))
            std_s3 = Paragraph(to_minutes_str(stds_s3[i], round_to=2))
            excluded_str = ""
            for ex in excl_laps[i]:
                excluded_str += str(ex) + ", "
            excluded_str = Paragraph(excluded_str[:-2])
            inv = Paragraph(str(len(invalid_stints[i])) + " (" + str(
                ((len(invalid_stints[i]) / total_laps[i]) * 100).__round__(1)) + "%)")
            inc = Paragraph(str(accidents[i]))
            strf = Paragraph(str(fuel_stints[i]))
            endf = Paragraph(str(fuel_stints_end[i]))
            tyr = Paragraph(tyres[i][0])
            data = [[im, 'Laps', lps, '', ''],
                    ['', 'Average laptime', avgl, '', ''],
                    ['', 'Standard deviation', stdl, '', ''],
                    ['', 'Average sectors', avg_s1, avg_s2, avg_s3],
                    ['', 'Standard deviation', std_s1, std_s2, std_s3],
                    ['', 'Excluded laps', excluded_str, '', ''],
                    ['', 'Invalid laps', inv, '', ''],
                    ['', 'Incidents', inc, '', ''],
                    ['', 'Starting fuel', strf, '', ''],
                    ['', 'Fuel left', endf, '', ''],
                    ['', 'Tyres used', tyr, '', '']]

            style = [
                ('GRID', (1, 0), (-1, -1), 0.25, colors.black),
                ('SPAN', (0, 0), (0, 10)),
                ('SPAN', (2, 0), (4, 0)),
                ('SPAN', (2, 1), (4, 1)),
                ('SPAN', (2, 2), (4, 2)),
                ('SPAN', (2, 5), (4, 5)),
                ('SPAN', (2, 6), (4, 6)),
                ('SPAN', (2, 7), (4, 7)),
                ('SPAN', (2, 8), (4, 8)),
                ('SPAN', (2, 9), (4, 9)),
                ('SPAN', (2, 10), (4, 10)),
                ('VALIGN', (0, 0), (0, 10), 'TOP')
            ]

            t = Table(data)
            t.setStyle(style)
            story.append(t)
            story.append(PageBreak())

        try:
            doc = SimpleDocTemplate(out_dir + "/" + filename + "_analysis.pdf")
            doc.build(story)
            print("Analysis successful, file " + filename + "_analysis.pdf" + " created")
            cwd = os.getcwd()
            os.chdir(out_dir)
            os.startfile(filename + "_analysis.pdf")
            os.chdir(cwd)
        except PermissionError:
            print("Saving file failed. Ensure you do not have the file open.")

    except ValueError or NameError or OSError:
        print("Error in analyzing the data. Some data may be invalid or missing.")

# Delete created images
[f.unlink() for f in Path(out_img_dir).glob("*") if f.is_file()]
