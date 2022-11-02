# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import unittest
import shutil
import subprocess
import hashlib
from pathlib import Path

PWD = os.path.dirname(os.path.realpath(__file__))
TEST_DIR = os.path.join(PWD, 'test')


def _update_format_env_variable():
    modified_env = os.environ.copy()
    modified_env['IMAGECMP'] = _join(PWD, 'imagecmp.py')
    return modified_env


def _init_test_dir():
    _remove_dir(TEST_DIR)
    Path(TEST_DIR).mkdir()


def _remove_dir(dir_path):
    shutil.rmtree(dir_path, ignore_errors=True)


def _copy_file(src, dest):
    Path(os.path.dirname(dest)).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


def _join(path_1, path_2):
    return os.path.join(path_1, path_2)


def _hashfile(file):
    buf_size = 65536
    sha256 = hashlib.sha256()
    with open(file, 'rb') as file:
        while True:
            data = file.read(buf_size)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def _copy_images_to_test_dir(images):
    for path, image_relative_path in images.items():
        src = _join(TEST_DIR, image_relative_path)
        dest = _join(TEST_DIR, path)
        _copy_file(src, dest)


def _create_sample_db(images, db_name):
    lines = []
    for path, image_relative_path in images.items():
        path = _join(TEST_DIR, path)
        image_full_path = _join(TEST_DIR, image_relative_path)
        hash_ = _hashfile(image_full_path)
        lines.append(f'{hash_} | {path}')

    file_path = _join(TEST_DIR, db_name)
    _write_lines_to_file(lines, file_path)


def _write_lines_to_file(lines, file_path):
    with open(file_path, 'w') as my_file:
        my_file.writelines(lines)


def _get_errors_from_file():
    errors_file_path = _join(TEST_DIR, 'errors')

    with open(errors_file_path, 'r') as err_file:
        raw_lines = err_file.readlines()
    lines = [line.strip() for line in raw_lines if line != '\n']

    num_of_lines = len(lines)
    duplicated_images = []

    idx = 0
    while idx < num_of_lines:
        line = lines[idx]

        if line == '❌':
            duplicated_images.append([lines[idx + 1], lines[idx + 2]])
            idx += 3
        else:
            idx += 1

    return duplicated_images


def _assert_errors_file_contains(self, lists_of_duplicated_files):
    errors_content = _get_errors_from_file()
    for file_1, file_2 in lists_of_duplicated_files:
        file_1_path = _join(TEST_DIR, file_1)
        file_2_path = _join(TEST_DIR, file_2)
        pair = [file_1_path, file_2_path]
        self.assertEqual(True, pair in errors_content)


def _read_db_lines(db_name):
    file_path = _join(TEST_DIR, db_name)
    with open(file_path, 'r') as my_file:
        lines = my_file.read().splitlines()
    return lines


def _assert_db_file_contains(self, db_name, lines):
    db_lines = _read_db_lines(db_name)
    for line in lines:
        self.assertEqual(True, line in db_lines)


def _assert_db_file_does_not_contains(self, db_name, lines):
    db_lines = _read_db_lines(db_name)
    for line in lines:
        self.assertEqual(False, line in db_lines)


class TestCompareImages(unittest.TestCase):

    def setUp(self):
        _init_test_dir()
        os.chdir(TEST_DIR)
        self._env = _update_format_env_variable()

    def tearDown(self):
        _remove_dir(TEST_DIR)

    def test_no_duplicated_images_found(self):
        images = {
            'image_1.jpg': '../../test_images/abstract_1.jpg',
            'image_2.jpg': '../../test_images/abstract_2.jpg',
            'image_3.jpg': '../../test_images/abstract_3.jpg',
        }
        _copy_images_to_test_dir(images)
        result = subprocess.run('imgcmp *',
                                shell=True,
                                check=True,
                                capture_output=True,
                                env=self._env)
        output = result.stdout.decode()
        self.assertEqual(True, "No duplicated files found" in output)

    def test_one_duplicated_image_found(self):
        images = {
            'image_1.jpg': '../../test_images/abstract_1.jpg',
            'image_2.jpg': '../../test_images/abstract_2.jpg',
            'image_3.jpg': '../../test_images/abstract_1.jpg',
        }
        _copy_images_to_test_dir(images)
        result = subprocess.run('imgcmp *',
                                shell=True,
                                check=True,
                                capture_output=True,
                                env=self._env)
        output = result.stdout.decode()
        self.assertEqual(True, "Duplicated files found" in output)
        _assert_errors_file_contains(self, [['image_3.jpg', 'image_1.jpg']])

    def test_two_duplicated_images_found(self):
        images = {
            'image_1.jpg': '../../test_images/abstract_1.jpg',
            'image_2.jpg': '../../test_images/abstract_1.jpg',
            'image_3.jpg': '../../test_images/abstract_1.jpg',
        }
        _copy_images_to_test_dir(images)
        result = subprocess.run('imgcmp *',
                                shell=True,
                                check=True,
                                capture_output=True,
                                env=self._env)
        output = result.stdout.decode()
        self.assertEqual(True, "Duplicated files found" in output)
        _assert_errors_file_contains(self,
                                     [['image_2.jpg', 'image_1.jpg'],
                                      ['image_3.jpg', 'image_1.jpg']])

    def test_find_duplicated_file_in_sub_dir(self):
        images = {
            'image_1.jpg': '../../test_images/abstract_1.jpg',
            'sub_dir/image_2.jpg': '../../test_images/abstract_1.jpg',
        }
        _copy_images_to_test_dir(images)
        result = subprocess.run('imgcmp -r *',
                                shell=True,
                                check=True,
                                capture_output=True,
                                env=self._env)
        output = result.stdout.decode()
        self.assertEqual(True, "Duplicated files found" in output)
        _assert_errors_file_contains(self,
                                     [['sub_dir/image_2.jpg', 'image_1.jpg']])

    def test_find_duplicated_file_exclude_dir(self):
        images = {
            'image_1.jpg': '../../test_images/abstract_1.jpg',
            'sub_dir_1/image_2.jpg': '../../test_images/abstract_1.jpg',
            'sub_dir_1/sub_dir_2/image_3.jpg': '../../test_images/abstract_1.jpg',
        }
        _copy_images_to_test_dir(images)
        result = subprocess.run('imgcmp -e sub_dir_1 -r *',
                                shell=True,
                                check=True,
                                capture_output=True,
                                env=self._env)
        output = result.stdout.decode()
        self.assertEqual(True, "No duplicated files found" in output)

    def test_find_duplicated_file_using_an_existing_database(self):
        images = {
            'sub_dir_1/image_1.jpg': '../../test_images/abstract_1.jpg',
            'sub_dir_2/image_2.jpg': '../../test_images/abstract_1.jpg',
        }
        _copy_images_to_test_dir(images)
        db_images = {
            'sub_dir_1/image_1.jpg': '../../test_images/abstract_1.jpg'}
        _create_sample_db(db_images, 'sample_database')
        result = subprocess.run('imgcmp -d sample_database sub_dir_2/*',
                                shell=True,
                                check=True,
                                capture_output=True,
                                env=self._env)
        output = result.stdout.decode()
        self.assertEqual(True, "Duplicated files found" in output)
        _assert_errors_file_contains(self,
                                     [['sub_dir_2/image_2.jpg',
                                       'sub_dir_1/image_1.jpg']])

    def test_database_clean_up_if_file_doesnt_exist(self):
        images = {
            'sub_dir_2/image_2.jpg': '../../test_images/abstract_1.jpg',
        }
        _copy_images_to_test_dir(images)
        db_images = {
            'sub_dir_1/image_1.jpg': '../../test_images/abstract_1.jpg'}
        _create_sample_db(db_images, 'sample_database')
        result = subprocess.run('imgcmp -d sample_database sub_dir_2/*',
                                shell=True,
                                check=True,
                                capture_output=True,
                                env=self._env)
        output = result.stdout.decode()
        self.assertEqual(True, "No duplicated files found" in output)
        expected_img_hash = _hashfile(_join(
            TEST_DIR, '../../test_images/abstract_1.jpg'))
        expected_img_path = _join(TEST_DIR, 'sub_dir_2/image_2.jpg')
        _assert_db_file_contains(self,
                                 'sample_database',
                                 [f'{expected_img_hash} | '
                                  f'{expected_img_path}'])
        not_expected_img_hash = _hashfile(_join(
            TEST_DIR, '../../test_images/abstract_1.jpg'))
        not_expected_img_path = _join(TEST_DIR, 'sub_dir_1/image_1.jpg')
        _assert_db_file_does_not_contains(self,
                                          'sample_database',
                                          [f'{not_expected_img_hash} | '
                                           f'{not_expected_img_path}'])


if __name__ == '__main__':
    unittest.main()
