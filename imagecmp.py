import os
import argparse
import hashlib
from natsort import natsorted

CWD = os.getcwd()
IS_RECURSIVE = False
EXCLUDE_DIRS = []
DATABASE = None
SUPPORTED_EXTENSIONS = ['jpg', 'mov', 'jpeg', 'mp4']


def hashfile(file):
    BUF_SIZE = 65536
    sha256 = hashlib.sha256()
    with open(file, 'rb') as file:
        while True:
            data = file.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def process(targets):
    files = []
    errors = []
    database_hashes, database_pairs = load_from_library()

    for target in targets:
        if os.path.isdir(target) and IS_RECURSIVE:
            files.extend(recursively_find_all_images_under(target))
        elif os.path.isfile(target):
            extension = target.rsplit('.', 1)[-1].lower()
            if extension in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(CWD, target))

    for file in natsorted(files):
        hash = hashfile(file)
        found_file = ''

        if hash in database_hashes:
            found_file = ''
            database_file = database_pairs[hash]
            if database_file != file:
                # check if database file still exists
                if os.path.exists(database_file):
                    found_file = database_file
                else:
                    # Old file no longer exists, remove it from the database
                    database_hashes.remove(hash)
                    del database_pairs[hash]

        if found_file:
            msg = (f'\n❌\n{file}\n{found_file}\n')
            print(msg)
            errors.append(msg)
            continue
        print(f'✅ {file}')
        database_hashes.add(hash)
        database_pairs[hash] = file

    with open(DATABASE, 'w') as file:
        for hash, path in sorted(database_pairs.items()):
            file.write(f'{hash} | {path}\n')

    if errors:
        with open('errors', 'w') as file:
                for err in errors:
                    file.write(f'{err}\n')
        print('\nDuplicated files found, see the "errors" file')
    else:
        print('\nNo Duplicated files found.')
    print('Done')


def load_from_library():
    hashes_set = set()
    pairs_dict = {}
    if os.path.exists(DATABASE):
        with open(DATABASE, 'r') as file:
            for line in file:
                pair = line.split('|', maxsplit=1)
                hash = pair[0].strip()
                path = pair[1].strip()
                hashes_set.add(hash)
                pairs_dict[hash] = path
    return hashes_set, pairs_dict


def recursively_find_all_images_under(directory):
    files_ = []
    for root, dirs, files in os.walk(os.path.join(CWD, directory)):
        dirs[:] = [dir for dir in dirs if dir not in EXCLUDE_DIRS]
        for file in files:
            full_path = os.path.join(root, file)
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
