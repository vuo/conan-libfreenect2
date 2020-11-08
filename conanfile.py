from conans import ConanFile, CMake, tools
import os
import platform
import shutil

class Libfreenect2Conan(ConanFile):
    name = 'libfreenect2'

    # libfreenect2 hasn't tagged a release in a while, so just use package_version.
    source_version = '0'
    package_version = '7'
    version = '%s-%s' % (source_version, package_version)

    build_requires = (
        'llvm/5.0.2-1@vuo/stable',
        'macos-sdk/11.0-0@vuo/stable',
    )
    requires = 'libusb/1.0.23-0@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/OpenKinect/libfreenect2'
    license = 'https://github.com/OpenKinect/libfreenect2/blob/master/APACHE20'
    description = 'Driver for the Kinect for Windows v2 / Kinect for Xbox One'
    source_dir = 'libfreenect2'
    generators = 'cmake'

    build_dir = '_build'
    install_dir = '_install'

    def requirements(self):
        if platform.system() == 'Linux':
            self.requires('patchelf/0.10pre-1@vuo/stable')
        elif platform.system() != 'Darwin':
            raise Exception('Unknown platform "%s"' % platform.system())

    def source(self):
        self.run("git clone https://github.com/OpenKinect/libfreenect2.git")
        with tools.chdir(self.source_dir):
            self.run("git checkout fd64c5d")

        tools.replace_in_file('%s/CMakeLists.txt' % self.source_dir,
                              'PROJECT(libfreenect2)',
                              '''
                              PROJECT(libfreenect2)
                              include(../conanbuildinfo.cmake)
                              conan_basic_setup()
                              ''')

        if platform.system() == 'Darwin':
            libext = 'dylib'
        elif platform.system() == 'Linux':
            libext = 'so'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        # Ensure libfreenect2 uses the version of libusb that we built.
        tools.replace_in_file('%s/CMakeLists.txt' % self.source_dir,
                              'FIND_PACKAGE(LibUSB REQUIRED)',
                              '''
                              SET(LibUSB_INCLUDE_DIRS ${CONAN_INCLUDE_DIRS_LIBUSB}/libusb-1.0)
                              SET(LibUSB_LIBRARIES ${CONAN_LIB_DIRS_LIBUSB}/lib${CONAN_LIBS_LIBUSB}.%s)
                              ''' % libext)

        self.run('mv %s/APACHE20 %s/%s.txt' % (self.source_dir, self.source_dir, self.name))

    def build(self):
        cmake = CMake(self)
        cmake.definitions['BUILD_EXAMPLES'] = False
        cmake.definitions['BUILD_OPENNI2_DRIVER'] = False
        cmake.definitions['BUILD_SHARED_LIBS'] = True
        cmake.definitions['CONAN_DISABLE_CHECK_COMPILER'] = True
        cmake.definitions['CMAKE_CXX_FLAGS'] = '-Oz -std=c++11 -stdlib=libc++'
        cmake.definitions['CMAKE_CXX_COMPILER'] = self.deps_cpp_info['llvm'].rootpath + '/bin/clang++'
        cmake.definitions['CMAKE_SHARED_LINKER_FLAGS'] = cmake.definitions['CMAKE_STATIC_LINKER_FLAGS'] = cmake.definitions['CMAKE_EXE_LINKER_FLAGS'] = '-stdlib=libc++ -lc++abi'
        cmake.definitions['CMAKE_INSTALL_PREFIX'] = '%s/%s' % (os.getcwd(), self.install_dir)
        if platform.system() == 'Darwin':
            cmake.definitions['CMAKE_OSX_ARCHITECTURES'] = 'x86_64;arm64'
            cmake.definitions['CMAKE_OSX_DEPLOYMENT_TARGET'] = '10.11'
            cmake.definitions['CMAKE_OSX_SYSROOT'] = self.deps_cpp_info['macos-sdk'].rootpath
        cmake.definitions['ENABLE_CUDA'] = False
        cmake.definitions['ENABLE_CXX11'] = True
        if platform.system() == 'Darwin':
            cmake.definitions['ENABLE_OPENCL'] = True
        cmake.definitions['ENABLE_OPENGL'] = False # Use the OpenCL packet processor, which is faster than the OpenGL packet processor.
        cmake.definitions['ENABLE_PROFILING'] = True
        cmake.definitions['ENABLE_TEGRAJPEG'] = False
        cmake.definitions['ENABLE_VAAPI'] = False

        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            cmake.configure(source_dir='../%s' % self.source_dir,
                            build_dir='.',
                            args=['-Wno-dev', '--no-warn-unused-cli'])
            cmake.build()
            cmake.install()

        with tools.chdir(self.install_dir):
            if platform.system() == 'Darwin':
                shutil.move('lib/libfreenect2.0.2.0.dylib', 'lib/libfreenect2.dylib')
                self.run('install_name_tool -id @rpath/libfreenect2.dylib lib/libfreenect2.dylib')
                self.run('install_name_tool -change @rpath/libc++.dylib /usr/lib/libc++.1.dylib lib/libfreenect2.dylib')
            elif platform.system() == 'Linux':
                shutil.move('lib/libfreenect2.so.0.2.0', 'lib/libfreenect2.so')
                patchelf = self.deps_cpp_info['patchelf'].rootpath + '/bin/patchelf'
                self.run('%s --set-soname libfreenect2.so lib/libfreenect2.so' % patchelf)

    def package(self):
        if platform.system() == 'Darwin':
            libext = 'dylib'
        elif platform.system() == 'Linux':
            libext = 'so'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        self.copy('*.h', src='%s/include' % self.install_dir, dst='include')
        self.copy('*.hpp', src='%s/include' % self.install_dir, dst='include')
        self.copy('libfreenect2.%s' % libext, src='%s/lib' % self.install_dir, dst='lib')
        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')

    def package_info(self):
        self.cpp_info.libs = ['freenect2']
