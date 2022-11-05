#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <list>
#include <map>
#include <string>
#include <set>
#include <vector>

#include "third-party/md5/md5.h"

std::filesystem::path kCwd;

std::filesystem::path GetCwd() { return std::filesystem::current_path(); }

long FindFileLength(std::ifstream& file) {
    file.seekg(0, std::ios::end);
    long len = file.tellg();
    file.seekg(0, std::ios::beg);
    return len;
}

std::string ReadFile(std::filesystem::path path) {
    std::ifstream input(path, std::ios::binary);
    std::vector<unsigned char> buffer(std::istreambuf_iterator<char>(input),
                                      {});
    std::string data(buffer.begin(), buffer.end());
    return data;
}

std::string GetFileHash(std::filesystem::path path) {
    std::string file_contents = ReadFile(path);
    std::string hash = md5(file_contents);
    std::cout << "hash = " << hash << std::endl;
    return hash;
}

void GetFileHashes(std::list<std::filesystem::path>& files,
                   std::map<std::filesystem::path, std::string>& hash_map) {
    std::list<std::filesystem::path>::iterator it;
    for (it = files.begin(); it != files.end(); ++it) {
        std::string hash = GetFileHash(*it);
        hash_map.insert({*it, hash});
        std::cout << "file = " << *it << " hash = " << hash_map.at(*it)
                  << std::endl;
    }
}

void GetListOfFiles(int argc, char* argv[],
                    std::list<std::filesystem::path>& files) {
    std::cout << "Number of arguments = " << argc << std::endl;

    for (int count = 1; count < argc; ++count) {
        std::cout << "[" << count << "] = " << argv[count] << std::endl;
        files.push_back(GetCwd() / argv[count]);
    }
}

bool FindDuplicates(std::map<std::filesystem::path, std::string>& hash_map) {
    std::set<std::string> unique_hashes;

    for (auto const& [path, hash] : hash_map) {

        if (unique_hashes.find(hash) != unique_hashes.end()) {
            return true;
        }
        unique_hashes.insert(hash);
    }

    return false;
}

int main(int argc, char* argv[]) {
    kCwd = GetCwd();
    std::map<std::filesystem::path, std::string> files_hashes;
    std::list<std::filesystem::path> files;

    GetListOfFiles(argc, argv, files);
    GetFileHashes(files, files_hashes);

    bool found_duplicates = FindDuplicates(files_hashes);

    if (found_duplicates) {
        std::system("echo 'Duplicated files found'");
    } else {
        std::system("echo 'No duplicated files found'");
    }

    return 0;
}
