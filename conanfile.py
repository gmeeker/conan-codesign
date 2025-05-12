import os

from conan import ConanFile
from conan.tools.apple import is_apple_os


class CodeSign:
    options = {
        "codesign": [False, True],
        "codesign_path": ["ANY", None],
        "codesign_identity": ["ANY", None],
        "codesign_store": ["ANY", None],
        "codesign_digest": ["ANY", None],
        "codesign_timestamp": ["ANY", None],
        "codesign_timestamp_digest": ["ANY", None],
        "codesign_flags": ["ANY", None],
    }
    default_options = {
        "codesign": False,
        "codesign_path": None,
        "codesign_identity": None,
        "codesign_store": "MY",
        "codesign_digest": "sha256",
        "codesign_timestamp": None,
        "codesign_timestamp_digest": "sha256",
        "codesign_flags": None,
    }

    def _vcvars_command(self):
        try:
            from conans import tools
            return tools.vcvars_command(self)
        except ImportError:
            # Conan 2
            from conan.tools.microsoft.visual import vcvars_command, vs_ide_version, _vcvars_versions, _vcvars_arch

            conanfile = self
            vs_install_path = conanfile.conf.get("tools.microsoft.msbuild:installation_path")
            vs_version, vcvars_ver = _vcvars_versions(conanfile)
            vcvarsarch = _vcvars_arch(conanfile)

            winsdk_version = conanfile.conf.get("tools.microsoft:winsdk_version", check_type=str)
            winsdk_version = winsdk_version or conanfile.settings.get_safe("os.version")
            vcvars = vcvars_command(vs_version, architecture=vcvarsarch, platform_type=None,
                                    winsdk_version=winsdk_version, vcvars_ver=vcvars_ver,
                                    vs_install_path=vs_install_path)
            return vcvars

    def verify(self, filename, verbose=False):
        if self.options.codesign or self.options.codesign_identity:
            if self.settings.os == "Windows":
                vcvars_command = self._vcvars_command()
                flags = '/v ' if verbose else '/q '
                self.run(f'{vcvars_command} && signtool verify {flags}"{filename}"')
            elif is_apple_os(self):
                flags = 'v' if verbose else ''
                self.run(f'codesign -v{flags} "{filename}"')

    @property
    def _signcmd(self):
        cmd = None
        identity = self.options.codesign_identity
        flags = self.options.codesign_flags or ""
        exts = []
        if self.options.codesign or identity:
            if self.settings.os == "Windows":
                signtool = self.options.codesign_path or 'signtool'
                cmd = f'{signtool} sign '
                if identity:
                    cmd += f'/n "{identity}" '
                else:
                    cmd += '/a '
                args = [
                    ('/s', self.options.codesign_store),
                    ('/fd', self.options.codesign_digest),
                    ('/tr', self.options.codesign_timestamp),
                    ('/td', self.options.codesign_timestamp_digest),
                ]
                for flag, value in args:
                    if value:
                        cmd += f"{flag} {value} "
            elif is_apple_os(self):
                codesign = self.options.codesign or 'codesign'
                if identity:
                    identity = f"Developer ID Application: {identity}"
                else:
                    identity = "-"
                cmd = f'{codesign} -s "{identity}" '
            if cmd and flags:
                cmd += flags + ' '
        return cmd

    def _codesign(self, cmd, filename):
        if self.settings.os == "Windows":
            vcvars_command = self._vcvars_command()
            self.run(f'{vcvars_command} && {cmd}"{filename}"')
        else:
            self.run(f'{cmd}"{filename}"')

    def codesign(self, basedir, filename=None, filenames=[]):
        cmd = self._signcmd
        if cmd:
            if os.path.isfile(basedir):
                self._codesign(cmd, basedir)
                return
            if self.settings.os == "Windows":
                exts = [".dll", ".exe"]
            elif is_apple_os(self):
                exts = [".dylib", ".bundle", ".framework", ".app"]
            if filename or filenames:
                exts = []
            if filename:
                filenames = list(filenames) + [filename]
            for root, dirs, files in os.walk(basedir):
                for f in files:
                    path = os.path.join(root, f)
                    basename = os.path.basename(path)
                    if (basename in filenames or os.path.splitext(path)[1] in exts) and not os.path.islink(path):
                        self._codesign(cmd, path)


class CodesignConan(ConanFile):
    name = "codesign"
    version = "1.0"
    license = "MIT"
    package_type = "python-require"
