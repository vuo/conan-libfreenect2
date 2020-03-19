from conans import ConanFile, CMake
import platform

class Libfreenect2TestConan(ConanFile):
    requires = 'llvm/3.3-5@vuo/stable'
    generators = 'cmake'

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy('*', src='lib', dst='lib')

    def test(self):
        self.run('./bin/test_package')

        # Ensure we only link to system libraries and to libraries we built.
        if platform.system() == 'Darwin':
            self.run('! (otool -L lib/libfreenect2.dylib | tail +3 | egrep -v "^\s*(/usr/lib/|/System/|@rpath/)")')
            self.run('! (otool -L lib/libfreenect2.dylib | fgrep "libstdc++")')
            self.run('! (otool -L lib/libfreenect2.dylib | fgrep "@rpath/libc++.dylib")')  # Ensure this library references the system's libc++.
            self.run('! (otool -l lib/libfreenect2.dylib | grep -A2 LC_RPATH | cut -d"(" -f1 | grep "\s*path" | egrep -v "^\s*path @(executable|loader)_path")')
        elif platform.system() == 'Linux':
            self.run('! (ldd lib/libfreenect2.so | grep -v "^lib/" | grep "/" | egrep -v "(\s(/lib64/|(/usr)?/lib/x86_64-linux-gnu/)|test_package/build|/\.conan/data/)")')
            self.run('! (ldd lib/libfreenect2.so | fgrep "libstdc++")')
        else:
            raise Exception('Unknown platform "%s"' % platform.system())
