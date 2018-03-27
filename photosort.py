import os
import exifread


def get_image():
    for (path, _, files) in os.walk(os.getcwd()):
        for f in files:
            yield f"{path}\\{f}"


def get_date_taken(image):
    with open(image, 'rb') as openimage:
        exiftags = exifread.process_file(openimage, details=False)
    return exiftags["EXIF DateTimeDigitized"]


images = get_image()
for i in range(3):
    print(get_date_taken(next(images)))
