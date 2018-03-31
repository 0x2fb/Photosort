import os
import exifread
from PIL import Image
import imagehash
import time
import shutil

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


def get_date_taken(imagefile):
    '''Returns the date the image was taken from its EXIF data'''
    with open(imagefile, 'rb') as image:
        exiftags = exifread.process_file(image, details=False)
    try:
        return exiftags["EXIF DateTimeOriginal"]
    except KeyError:
        return time.strftime(
            "%Y:%m:%d %H:%M:%S", time.gmtime(os.path.getmtime(imagefile))
        )


def get_image_size(imagefile):
    '''Returns a tuple (w, h) that holds the width and height of an image'''
    image = Image.open(imagefile)
    return image.size


def get_file_size(imagefile):
    '''Returns size of the image in Bytes'''
    return os.path.getsize(imagefile)


def get_filename(imagefile):
    '''Returns the filename of the image'''
    return os.path.basename(imagefile)


def get_hash_values(imagefile):
    '''Returns the hash values of image with rotation'''
    image = Image.open(imagefile)
    hash_values = []
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    return hash_values


def create_folder(time_unit, folder=basefolder):
    '''Creates a folder based on a unit of time'''
    if not os.path.exists(os.path.join(folder, time_unit)):
        os.makedirs(os.path.join(folder, time_unit))


def move_image(imagefile, time):
    '''Moves and renames the image to a folder
    based on EXIF DateTimeOriginal'''
    (year, month, day), (hour, minutes, seconds) = (x.split(':')
                                                    for x in time.split())
    create_folder(year)
    create_folder(month, os.path.join(basefolder, year))
    new_filename = f'{day}.{month}.{year} {hour}-{minutes}-{seconds}.'
    f'{os.path.splitext(imagefile)[1]}'
    shutil.move(imagefile, os.path.join(basefolder, year, month, new_filename))


images = get_image()
for i in range(77):
    image = next(images)
    print(get_filename(image))
    # print(get_date_taken(image))
    # print(get_image_size(image))
    # print(get_file_size(image))
    # print(get_hash_values(image))
    # move_image(image, str(get_date_taken(image)))
    # print(image)
    # print(os.path.splitext(image))
