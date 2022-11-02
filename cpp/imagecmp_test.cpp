#include <gtest.h>

#include <filesystem>
#include <map>

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
    std::string test_dir = "test_dir";

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
        return GetCwd() / std::filesystem::path(test_dir);
    }
};

TEST_F(SampleTest, BasicAssertions) {
    std::string result = Exec("echo Hello World");
    std::string expected = "\nHello World\n";
    EXPECT_EQ(expected, result);
    EXPECT_EQ(7 * 6, 42);
}

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

    std::string result = Exec("imgcmp *");
    EXPECT_EQ(true,
              result.find("No duplicated files found") != std::string::npos);
}
