import csv
import math

from reportlab.lib import utils
from reportlab.platypus import Image


decimal_delim = ','


def to_seconds(time):
    t = time.split(':')
    if t[0] == "":
        return math.inf
    mins = float(t[0])
    secs = t[1].split(decimal_delim)
    return mins*60+float(secs[0])+float(secs[1])/1000


def to_minutes_str(time):
    mins = int(time // 60)
    secs = (time % 60).__round__(3)
    if mins == 0:
        return str(secs)
    return str(mins) + ":" + str(secs)


def to_liters(fuel):
    f = fuel.strip('L').split(decimal_delim)
    return float(f[0])+float(f[1])/10


def data_reader(data_dir, filename):
    r1 = None
    laps = []
    with open(data_dir + '/' + filename, newline='') as csvfile:
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
