import os

from conans import ConanFile, tools
from conans.client.tools.apple import is_apple_os


class CodeSign:
    options = {
        "codesign": [False, True],
        "codesign_path": "ANY",
        "codesign_identity": "ANY",
        "codesign_store": "ANY",
        "codesign_digest": "ANY",
        "codesign_timestamp": "ANY",
        "codesign_timestamp_digest": "ANY",
        "codesign_flags": "ANY",
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

    def verify(self, filename, verbose=False):
        if self.options.codesign or self.options.codesign_identity:
            if self.settings.os == "Windows":
                vcvars_command = tools.vcvars_command(self)
                flags = '/v ' if verbose else '/q '
                self.run(f'{vcvars_command} && signtool verify {flags}"{filename}"')
            elif is_apple_os(self.settings.os):
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
            elif is_apple_os(self.settings.os):
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
            vcvars_command = tools.vcvars_command(self)
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
            elif is_apple_os(self.settings.os):
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
