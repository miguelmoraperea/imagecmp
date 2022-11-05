#include <gtest.h>

#include <filesystem>
#include <map>

std::string kTarget = "./buck-out/gen/imagecmp";
std::string kTestDir = "test_dir";

class SampleTest : public ::testing::Test {
   protected:
    void SetUp() override {
        RemoveTestDirectory();
        CreateTestDirectory();
    }

    void TearDown() override { RemoveTestDirectory(); }

    std::string Exec(std::string cmd) {
        std::array<char, 128> buffer = {0};
        std::string result = "\n";

        std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"),
                                                      pclose);
        if (!pipe) {
            throw std::runtime_error("Pipe failed to open");
        }
        while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
            result += buffer.data();
        }
        return result;
    }

    void CopyImagesToTestDir(std::map<std::string, std::string> images_map) {
        std::map<std::string, std::string>::iterator it;

        for (it = images_map.begin(); it != images_map.end(); it++) {
            std::string src =
                JoinPaths(GetCwd(), std::filesystem::path(it->second));
            std::string dest =
                JoinPaths(GetTestDir(), std::filesystem::path(it->first));
            CopyFile(src, dest);
        }
    }

   private:
    void CreateTestDirectory() { Exec("mkdir " + GetTestDir().string()); }

    void RemoveTestDirectory() { Exec("rm -rf " + GetTestDir().string()); }

    void CopyFile(std::string src, std::string dest) {
        std::string cmd = "cp " + src + " " + dest;
        std::cout << Exec(cmd) << std::endl;
    }

    std::filesystem::path JoinPaths(std::filesystem::path path_1,
                                    std::filesystem::path path_2) {
        return path_1 / path_2;
    }

    std::filesystem::path GetCwd() { return std::filesystem::current_path(); }

    std::filesystem::path GetTestDir() {
        return GetCwd() / std::filesystem::path(kTestDir);
    }
};

TEST_F(SampleTest, TestNoDuplicatedImagesFound) {
    std::map<std::string, std::string> images_map = {
        {
            "image_1.jpg",
            "../test_images/abstract_1.jpg",
        },
        {
            "image_2.jpg",
            "../test_images/abstract_2.jpg",
        },
        {
            "image_3.jpg",
            "../test_images/abstract_3.jpg",
        }};
    CopyImagesToTestDir(images_map);

    std::string result = Exec(kTarget + " " + kTestDir + "/*");
    EXPECT_EQ(true,
              result.find("No duplicated files found") != std::string::npos);
}

TEST_F(SampleTest, TestOneDuplicatedFileFound) {
    std::map<std::string, std::string> images_map = {
        {
            "image_1.jpg",
            "../test_images/abstract_1.jpg",
        },
        {
            "image_2.jpg",
            "../test_images/abstract_2.jpg",
        },
        {
            "image_3.jpg",
            "../test_images/abstract_1.jpg",
        }};
    CopyImagesToTestDir(images_map);

    std::string result = Exec(kTarget + " " + kTestDir + "/*");
    std::cout << result << std::endl;
    EXPECT_EQ(true, result.find("Duplicated files found") != std::string::npos);
}
