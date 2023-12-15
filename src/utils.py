import csv
import math
import locale

from reportlab.lib import utils
from reportlab.platypus import Image

locale.setlocale(locale.LC_ALL, '')
decimal_delim = locale.localeconv()['mon_decimal_point']


def to_seconds(time):
    t = time.split(':')
    if t[0] == "":
        return math.inf
    mins = float(t[0])
    secs = t[1].split(decimal_delim)
    return mins*60+float(secs[0])+float(secs[1])/1000


def to_minutes_str(time, round_to=3):
    mins = int(time // 60)
    secs = (time % 60).__round__(round_to)
    if mins == 0:
        return str(secs)
    return str(mins) + ":" + str(secs)


def to_liters(fuel):
    f = fuel.strip('L').split(decimal_delim)
    return float(f[0])+float(f[1])/10


def data_reader(data_dir, filename):
    r1 = None
    laps = []
    with open(data_dir + '/' + filename, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            if r1 is None:
                r1 = row
            else:
                laps.append(row)
    return r1, laps


def get_image(path, width):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))


def condition_to_int(cond):
    if cond == "Optimum":
        return 6
    elif cond == "Fast":
        return 5
    elif cond == "Green":
        return 4
    elif cond == "Greasy":
        return 3
    elif cond == "Damp":
        return 2
    elif cond == "Wet":
        return 1
    elif cond == "Flooded":
        return 0
    else:
        return -1


def int_to_condition(cond):
    if cond == 6:
        return "Optimum"
    elif cond == 5:
        return "Fast"
    elif cond == 5:
        return "Green"
    elif cond == 3:
        return "Greasy"
    elif cond == 2:
        return "Damp"
    elif cond == 1:
        return "Wet"
    elif cond == 0:
        return "Flooded"
    else:
        return ""


def rain_to_int(rain):
    if rain == "Heavy Rain":
        return 3
    elif rain == "Medium Rain":
        return 2
    elif rain == "Light Rain":
        return 1
    elif rain == "No Rain":
        return 0
    else:
        return -1


def int_to_rain(rain):
    if rain == 3:
        return "Heavy Rain"
    elif rain == 2:
        return "Medium Rain"
    elif rain == 1:
        return "Light Rain"
    elif rain == 0:
        return "No Rain"
    else:
        return ""


def gap_to_float(gap):
    gap = gap[1:]
    gap = gap.replace(decimal_delim, ".")
    return float(gap)


def get_track_map(track_dir, track, width):
    name = track.split("(")[0].strip(" ")
    return get_image(track_dir + "/" + name + ".png", width)


def secs_to_mins(secs):
    mins = []
    for sec in secs:
        mins.append(to_minutes_str(sec))
    return mins


def condition_ticks(ticks):
    new_ticks = []
    for t in ticks:
        new_ticks.append(int_to_condition(t))
    return new_ticks


def rain_ticks(ticks):
    new_ticks = []
    for t in ticks:
        new_ticks.append(int_to_rain(t))
    return new_ticks


def temps_to_float(temps):
    new_temps = []
    for t in temps:
        new_temps.append(float(t.split("°")[0][:-1].replace(decimal_delim, ".")))
    return new_temps


