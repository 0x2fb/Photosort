import os
import exifread
from PIL import Image
import imagehash
import time
import shutil
import sqlite3
import re
import piexif

basefolder = os.path.dirname(os.path.abspath(__file__))

# ========================= DATABASE FUNCTIONS =========================


def create_tables(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY, filename TEXT)")
    db.execute(
        "CREATE TABLE IF NOT EXISTS image_info (image INTEGER PRIMARY KEY, date_taken TEXT, img_size TEXT, file_size TEXT)")
    db.execute(
        "CREATE TABLE IF NOT EXISTS hash_values (image INTEGER PRIMARY KEY, hashes TEXT)")
    db.execute(
        "CREATE VIEW IF NOT EXISTS image_list AS SELECT images.id, images.filename, image_info.date_taken, image_info.img_size, "
        "image_info.file_size, hash_values.hashes FROM images INNER JOIN "
        "image_info ON images.id = image_info.image INNER JOIN hash_values ON images.id = hash_values.image")


def write_to_db(hashes, filename, date_taken, img_size, file_size, db):
    '''Inserts the image data into the database'''
    db.execute("INSERT INTO images(id, filename) VALUES(NULL, ?)",
               (filename,))
    db.execute("INSERT INTO image_info(image, date_taken, img_size, file_size) VALUES(NULL, ?, ?, ?)",
               (date_taken, img_size, file_size))
    db.execute("INSERT INTO hash_values(image , hashes) VALUES(NULL, ?)",
               (hashes,))
    db.commit()


def compare(hashes, db):
    cursor = db.execute(
        "SELECT count(*) FROM hash_values WHERE hashes = ?", (hashes,))
    return cursor.fetchone()[0]

# ========================= EXIF FUNCTIONS =========================


def get_date_taken(imagefile):
    '''Returns the date the image was taken from its EXIF data.
    Returns last modified date if there is no EXIF data.'''
    with open(imagefile, 'rb') as image:
        exiftags = exifread.process_file(image, details=False)
    try:
        return exiftags["EXIF DateTimeOriginal"]
    except KeyError:
        img_time = contains_date(imagefile)
        if img_time:
            write_exif(imagefile, img_time)
            return img_time
        else:
            img_time = get_changedate(imagefile)
            write_exif(imagefile, img_time)
            return img_time


def get_changedate(imagefile):
    return time.strftime("%Y:%m:%d %H:%M:%S", time.gmtime(os.path.getmtime(imagefile)))


def contains_date(imagefile):
    '''Regex Check for Dates and times starting or ending with year 20xx'''
    imagefile = get_filename(imagefile)
    pattern1 = re.compile(
        r'([0-3]\d)[\.\-_]?([01]\d)[\.\-_]?(20\d\d)[\-_ ]([0-2]\d)[\.\-_]?([0-5]\d)[\.\-_]?([0-5]\d)')
    match = pattern1.search(imagefile)
    if match:
        day, month, year, hour, minute, second = match.groups()
        return f'{year}:{month}:{day} {hour}:{minute}:{second}'
    else:
        pattern2 = re.compile(
            r'(20\d\d)[\.\-_]?([01]\d)[\.\-_]?([0-3]\d)[\-_ ]([0-2]\d)[\.\-_]?([0-5]\d)[\.\-_]?([0-5]\d)')
        match = pattern2.search(imagefile)
        if match:
            year, month, day, hour, minute, second = match.groups()
            return f'{year}:{month}:{day} {hour}:{minute}:{second}'


def write_exif(imagefile, img_time):
    if imagefile.lower().endswith(('.jpg', '.jpeg')):
        exif_dict = piexif.load(imagefile)
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = img_time
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = img_time
        exif_dict['0th'][piexif.ImageIFD.DateTime] = img_time
        try:
            exif_bytes = piexif.dump(exif_dict)
        except ValueError:
            print("Could not write EXIF data")
        else:
            im = Image.open(imagefile)
            im.save(imagefile, exif=exif_bytes)

# ========================= INFORMATION RETRIEVAL FUNCTIONS =========================


def get_img_size(image):
    '''Returns a tuple (w, h) that holds the width and height of an image'''
    return "{} x {}".format(*sorted(list(image.size), reverse=True))


def get_file_size(imagefile):
    '''Returns size of the image in Bytes'''
    return os.path.getsize(imagefile)


def get_filename(imagefile):
    '''Returns the filename of the image'''
    return os.path.basename(imagefile)


def get_hash_values(image):
    '''Returns the hash values of the image with rotation'''
    hash_values = []
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    image = image.rotate(90, expand=True)
    hash_values.append(str(imagehash.phash(image)))
    return ''.join(sorted(hash_values))

# ========================= FILE MOVE FUNCTIONS =========================


def create_folder(time_unit, folder=basefolder):
    '''Creates a folder based on a unit of time'''
    if not os.path.exists(os.path.join(folder, time_unit)):
        os.makedirs(os.path.join(folder, time_unit))


def move_image(imagefile, img_time):
    '''Moves and renames the image to a folder
    based on EXIF DateTimeOriginal'''
    try:
        (year, month, day), (hour, minutes, seconds) = (x.split(':')
                                                        for x in img_time.split())
    except ValueError:
        print(f'ERROR: {imagefile} has wrong date format.')
    else:
        create_folder(year)
        create_folder(month, os.path.join(basefolder, year))
        new_filename = f'{day}.{month}.{year} {hour}-{minutes}-{seconds}{os.path.splitext(imagefile)[1]}'
        new_folder = os.path.join(basefolder, year, month, new_filename)
        for _ in range(5):
            try:
                shutil.move(imagefile, new_folder)
            except WindowsError:
                time.sleep(0.1)
            else:
                break

# ========================= FILE FUNCTIONS =========================


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


def check_hash(image, db):
    hashes = get_hash_values(image)
    if compare(hashes, db) < 1:
        return hashes
    else:
        return None


def process_image(imagefile, db):
    try:
        with Image.open(imagefile) as image:
            unique_hash = check_hash(image, db)
            if unique_hash:
                img_size = get_img_size(image)
            else:
                print(f'{imagefile} is a duplicate.')
        if unique_hash:
            filename = get_filename(imagefile)
            date_taken = str(get_date_taken(imagefile))
            file_size = str(get_file_size(imagefile))
            write_to_db(unique_hash, filename, date_taken,
                        img_size, file_size, db)
            move_image(imagefile, date_taken)
    except OSError:
        print(f"Unable to open {imagefile}.")


if __name__ == '__main__':
    images = get_image()
    with sqlite3.connect(os.path.join(basefolder, 'img_db.sqlite')) as img_db:
        create_tables(img_db)
        for image in images:
            print(get_filename(image))
            process_image(image, img_db)
            # write_to_db(image, img_db)
            # print(get_date_taken(image))
            # print(get_img_size(image))
            # print(get_file_size(image))
            # print(compare(get_hash_values(image), img_db))
            # print(get_hash_values(image))
            # move_image(image, str(get_date_taken(image)))
            # print(image)
            # print(os.path.splitext(image))
