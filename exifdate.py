import os
import piexif
import time
from PIL import Image

basefolder = os.path.dirname(os.path.abspath(__file__))


def get_image(folder=basefolder):
    '''Generator object that yields all images
    of a folder and its subfolders'''

    def is_image(file):
        '''Returns True if the file is an image'''
        return file.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp', '.gif'))

    for (path, _, files) in os.walk(folder):
        for f in files:
            if is_image(f):
                yield os.path.join(path, f)


images = get_image()
for image in images:
    ctime = time.strftime(
        "%Y:%m:%d %H:%M:%S", time.gmtime(os.path.getmtime(image))
    )
    exif_dict = piexif.load(image)
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = ctime
    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = ctime
    exif_dict['0th'][piexif.ImageIFD.DateTime] = ctime
    print(exif_dict)
    exif_bytes = piexif.dump(exif_dict)
    im = Image.open(image)
    im.save(image, exif=exif_bytes)
