# Conan python requires that performs code signing

## profile

Add code signing identity as an option, probably to all recipes that support it.

```
[options]
*:codesign_identity=Garrick Meeker
```

## Using in recipes

```
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
        cmake.configure()
        cmake.build()
        self.codesign(self.build_folder, filenames=["test_package", "test_package.exe"])
```

Alternatively, have package() automatically sign binaries:
```
class CodeSignTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    python_requires = "codesign/1.0"
    python_requires_extend = "codesign.CodeSign"

    def init(self):
        base = self.python_requires["codesign"].module.CodeSign
        self.options = base.options
        self.default_options = base.default_options

    def package(self):
        ...
        self.codesign(self.package_folder)
```
