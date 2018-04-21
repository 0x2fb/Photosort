import os
import exifread
from PIL import Image
import imagehash
import time
import shutil
import sqlite3

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


def get_img_size(imagefile):
    '''Returns a tuple (w, h) that holds the width and height of an image'''
    image = Image.open(imagefile)
    return "{} x {}".format(*sorted(list(image.size), reverse=True))


def get_file_size(imagefile):
    '''Returns size of the image in Bytes'''
    return os.path.getsize(imagefile)


def get_filename(imagefile):
    '''Returns the filename of the image'''
    return os.path.basename(imagefile)


def get_hash_values(imagefile):
    '''Returns the hash values of the image with rotation'''
    image = Image.open(imagefile)
    hash_values = []
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    return ''.join(sorted(hash_values))


def write_to_db(imagefile, db):
    '''Inserts the image data into the database'''
    hashes = get_hash_values(imagefile)
    if compare(hashes, db) < 1:
        filename = get_filename(imagefile)
        date_taken = str(get_date_taken(imagefile))
        img_size = get_img_size(imagefile)
        file_size = str(get_file_size(imagefile))

        db.execute("INSERT INTO images(id, filename) VALUES(NULL, ?)",
                   (filename,))
        db.execute("INSERT INTO image_info(image, date_taken, img_size, file_size) VALUES(NULL, ?, ?, ?)",
                   (date_taken, img_size, file_size))
        db.execute("INSERT INTO hash_values(image , hashes) VALUES(NULL, ?)",
                   (hashes,))
        db.commit()
    else:
        print("Duplicate Found!")


def compare(hashes, db):
    cursor = db.execute(
        "SELECT count(*) FROM hash_values WHERE hashes = ?", (hashes,))
    return cursor.fetchone()[0]


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
    new_filename = f'{day}.{month}.{year} {hour}-{minutes}-{seconds}.{os.path.splitext(imagefile)[1]}'
    shutil.move(imagefile, os.path.join(basefolder, year, month, new_filename))


images = get_image()
img_db = sqlite3.connect(os.path.join(basefolder, 'img_db.sqlite'))
img_db.execute(
    "CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY, filename TEXT)")
img_db.execute(
    "CREATE TABLE IF NOT EXISTS image_info (image INTEGER PRIMARY KEY, date_taken TEXT, img_size TEXT, file_size TEXT)")
img_db.execute(
    "CREATE TABLE IF NOT EXISTS hash_values (image INTEGER PRIMARY KEY, hashes TEXT)")
img_db.execute(
    "CREATE VIEW IF NOT EXISTS image_list AS SELECT images.id, images.filename, image_info.date_taken, image_info.img_size, "
    "image_info.file_size, hash_values.hashes FROM images INNER JOIN "
    "image_info ON images.id = image_info.image INNER JOIN hash_values ON images.id = hash_values.image"
)
for i in range(78):
    image = next(images)
    print(get_filename(image))
    write_to_db(image, img_db)
    print(get_date_taken(image))
    print(get_img_size(image))
    print(get_file_size(image))
    print(compare(get_hash_values(image), img_db))
    # print(get_hash_values(image))
    # move_image(image, str(get_date_taken(image)))
    # print(image)
    # print(os.path.splitext(image))
img_db.close()
