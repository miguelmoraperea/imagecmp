#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <list>
#include <map>
#include <set>
#include <string>
#include <vector>

#include "third-party/md5/md5.h"

class File {
   public:
    File(std::filesystem::path path) : path(path) {
        std::string file_contents = Read();
        hash = md5(file_contents);
    }

    std::string Hash() { return hash; }

    std::filesystem::path Path() { return path; }

   private:
    std::filesystem::path path;
    std::string hash;

    std::string Read() {
        std::ifstream input(path, std::ios::binary);
        std::vector<unsigned char> buffer(std::istreambuf_iterator<char>(input),
                                          {});
        std::string data(buffer.begin(), buffer.end());
        return data;
    }
};

std::filesystem::path GetCwd() { return std::filesystem::current_path(); }

void GetListOfFiles(int argc, char* argv[], std::list<File>& files) {
    for (int count = 1; count < argc; ++count) {
        files.push_back(File(GetCwd() / argv[count]));
    }
}

bool FindDuplicates(std::list<File>& files) {
    std::set<std::string> unique_hashes;

    for (auto& file : files) {
        std::string hash = file.Hash();
        if (unique_hashes.find(hash) != unique_hashes.end()) {
            return true;
        }
        unique_hashes.insert(hash);
    }

    return false;
}

int main(int argc, char* argv[]) {
    std::list<File> files;

    GetListOfFiles(argc, argv, files);
    bool found_duplicates = FindDuplicates(files);

    if (found_duplicates) {
        std::system("echo 'Duplicated files found'");
    } else {
        std::system("echo 'No duplicated files found'");
    }

    return 0;
}
