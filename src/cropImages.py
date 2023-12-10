# Importing Image class from PIL module
from PIL import Image
import os

car_dir = 'cars'

# get the path/directory
for image in os.listdir(car_dir):
    # check if the image ends with png
    if image.endswith(".png"):
        print(image)
        # Opens a image in RGB mode
        im = Image.open(car_dir + "/" + image)

        # Size of the image in pixels (size of original image)
        # (This is not mandatory)
        width, height = im.size

        # Setting the points for cropped image

        top = 270
        bottom = 1020
        h = bottom - top
        w = int(16/9*h)
        left = 705
        right = left + w

        # Cropped image of above dimension
        # (It will not change original image)
        im1 = im.crop((left, top, right, bottom))

        # Shows the image in image viewer

        im1.save(image)

