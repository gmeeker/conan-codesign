import os

from conans import ConanFile, CMake, tools


class CodeSignTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    python_requires = "codesign/1.0"
    python_requires_extend = "codesign.CodeSign"

    def init(self):
        base = self.python_requires["codesign"].module.CodeSign
        self.options = base.options
        self.default_options = base.default_options

    def build(self):
        cmake = CMake(self)
        # Current dir is "test_package/build/<build_id>" and CMakeLists.txt is
        # in "test_package"
        cmake.configure()
        cmake.build()
        self.codesign(self.build_folder, filenames=["test_package", "test_package.exe"])

    def test(self):
        bin_path = os.path.join("bin", "test_package")
        if not tools.cross_building(self.settings):
            self.run(bin_path, run_environment=True)
        self.verify(bin_path, verbose=True)
