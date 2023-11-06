from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout
import os


class CodeSignTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeToolchain", "CMakeDeps", "VirtualRunEnv"
    python_requires = "codesign/1.0"
    python_requires_extend = "codesign.CodeSign"

    def init(self):
        base = self.python_requires["codesign"].module.CodeSign
        try:
            self.options.update(base.options, base.default_options)
        except TypeError:
            # Needed for compatibility with v1.x - Remove when 2.0 becomes the default
            self.options = base.options
            self.default_options = base.default_options

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        self.codesign(self.build_folder, filenames=["test_package", "test_package.exe"])

    def test(self):
        bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package")
        if can_run(self):
            self.run(bin_path)
        self.verify(bin_path, verbose=True)
