import os
import exifread
from PIL import Image


def get_image():
    '''Generator object that yields all images [todo]
    in a folder and its subfolders'''
    for (path, _, files) in os.walk(os.getcwd()):
        for f in files:
            yield f"{path}\\{f}"


def get_date_taken(imagefile):
    '''Returns the date the image was taken from its EXIF data'''
    with open(imagefile, 'rb') as image:
        exiftags = exifread.process_file(image, details=False)
    return exiftags["EXIF DateTimeOriginal"]


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


images = get_image()
for i in range(3):
    image = next(images)
    print(get_filename(image))
    print(get_date_taken(image))
    print(get_image_size(image))
    print(get_file_size(image))
