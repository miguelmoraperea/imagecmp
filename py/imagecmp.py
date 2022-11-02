# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import argparse
import hashlib
from natsort import natsorted

CWD = os.getcwd()
IS_RECURSIVE = False
EXCLUDE_DIRS = []
DATABASE = None
SUPPORTED_EXTENSIONS = ['jpg', 'mov', 'jpeg', 'mp4']


def join(path_1, path_2):
    return os.path.join(path_1, path_2)


def exists(path):
    return os.path.exists(path)


def hashfile(file):
    buf_size = 65536
    sha256 = hashlib.sha256()
    with open(file, 'rb') as my_file:
        while True:
            data = my_file.read(buf_size)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def is_under_excluded_dirs(path):
    for directory in EXCLUDE_DIRS:
        if directory in path.split('/'):
            return True
    return False


def find_files(targets):
    files = []
    for target in targets:
        if is_under_excluded_dirs(target):
            continue
        if os.path.isdir(target) and IS_RECURSIVE:
            files.extend(recursively_find_all_images_under(target))
        elif os.path.isfile(target):
            extension = target.rsplit('.', 1)[-1].lower()
            if extension in SUPPORTED_EXTENSIONS:
                files.append(join(CWD, target))
    return files


def save_database(database_pairs):
    with open(DATABASE, 'w') as file:
        for hash_, path in sorted(database_pairs.items()):
            file.write(f'{hash_} | {path}\n')


def output_results(errors):
    if errors:
        with open('errors', 'w') as file:
            for err in errors:
                file.write(f'{err}\n')
        print('\nDuplicated files found, see the "errors" file')
    else:
        print('\nNo duplicated files found.')
    print('Done')


def check_for_duplicates(files, db_hashes, db_pairs):
    errors = []
    for file in natsorted(files):
        hash_ = hashfile(file)
        found_file = ''
        if hash_ in db_hashes:
            db_file = db_pairs[hash_]
            if db_file != file:
                # check if database file still exists
                if exists(db_file):
                    found_file = db_file
                else:
                    # Old file no longer exists, remove it from the database
                    db_hashes.remove(hash_)
                    del db_pairs[hash_]

        if found_file:
            msg = (f'\n❌\n{file}\n{found_file}\n')
            print(msg)
            errors.append(msg)
            continue
        print(f'✅ {file}')
        db_hashes.add(hash_)
        db_pairs[hash_] = file
    return errors


def process(targets):
    errors = []
    db_hashes, db_pairs = load_from_library()
    files = find_files(targets)
    errors = check_for_duplicates(files, db_hashes, db_pairs)
    save_database(db_pairs)
    output_results(errors)


def load_from_library():
    hashes_set = set()
    pairs_dict = {}
    if exists(DATABASE):
        with open(DATABASE, 'r') as my_file:
            for line in my_file:
                pair = line.split('|', maxsplit=1)
                hash_ = pair[0].strip()
                path = pair[1].strip()
                hashes_set.add(hash_)
                pairs_dict[hash_] = path
    return hashes_set, pairs_dict


def recursively_find_all_images_under(directory):
    files_ = []
    for root, dirs, files in os.walk(join(CWD, directory)):
        dirs[:] = [dir for dir in dirs if not is_under_excluded_dirs(dir)]
        for file in files:
            full_path = join(root, file)
            extension = get_extension(full_path)
            if extension is not None and extension in SUPPORTED_EXTENSIONS:
                files_.append(full_path)
    return files_


def get_extension(path):
    if '.' in path:
        return path.rsplit('.', 1)[-1].lower()
    return None


def main():
    global IS_RECURSIVE
    global EXCLUDE_DIRS
    global DATABASE

    parser = argparse.ArgumentParser(description='Reformat file names')
    parser.add_argument('targets', nargs='+', help='Targets to rename')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Apply reformatting recursively')
    parser.add_argument('-e', '--exclude_dirs', nargs=1, default=[],
                        help='Exclude the directories that match')
    parser.add_argument('-d', '--database', nargs=1, default=['img_database'],
                        help='Path to the hashes database')

    args = parser.parse_args()

    IS_RECURSIVE = args.recursive
    EXCLUDE_DIRS = args.exclude_dirs
    DATABASE = args.database[0]

    process(args.targets)


if __name__ == '__main__':
    main()
