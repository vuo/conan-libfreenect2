from conans import ConanFile, CMake, tools

class Libfreenect2Conan(ConanFile):
    name = 'libfreenect2'
    version = '0.2.0'
    requires = 'libusb/1.0.21@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://bintray.com/vuo/conan/libfreenect2%3Avuo'
    license = 'https://github.com/OpenKinect/libfreenect2/blob/master/APACHE20'
    description = 'Driver for the Kinect for Windows v2 / Kinect for Xbox One'
    source_dir = 'libfreenect2-%s' % version
    build_dir = '_build'
    dylib_name = 'libfreenect2.%s.dylib' % version
    generators = 'cmake'

    def source(self):
        tools.get('https://github.com/OpenKinect/libfreenect2/archive/v%s.tar.gz' % self.version,
                  # sha256='344019f4360d3858f4c5843e215b0b9d0c0d396a2ebe5cb1953c262df4d9ff54'
                  )

        tools.replace_in_file('%s/CMakeLists.txt' % self.source_dir,
                              'PROJECT(libfreenect2)',
                              '''
                              PROJECT(libfreenect2)
                              include(../conanbuildinfo.cmake)
                              conan_basic_setup()
                              ''')

        # Ensure libfreenect2 uses the version of libusb that we built.
        tools.replace_in_file('%s/CMakeLists.txt' % self.source_dir,
                              'FIND_PACKAGE(LibUSB REQUIRED)',
                              '''
                              SET(LibUSB_INCLUDE_DIRS ${CONAN_INCLUDE_DIRS_LIBUSB}/libusb-1.0)
                              SET(LibUSB_LIBRARIES ${CONAN_LIB_DIRS_LIBUSB}/lib${CONAN_LIBS_LIBUSB}.dylib)
                              ''')

    def build(self):
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            cmake = CMake(self)
            cmake.definitions['BUILD_EXAMPLES'] = False
            cmake.definitions['BUILD_OPENNI2_DRIVER'] = False
            cmake.definitions['BUILD_SHARED_LIBS'] = True
            cmake.definitions['CMAKE_CXX_COMPILER'] = '/usr/local/bin/clang++'
            cmake.definitions['CMAKE_CXX_FLAGS'] = '-Oz -mmacosx-version-min=10.8'
            cmake.definitions['ENABLE_CUDA'] = False
            cmake.definitions['ENABLE_CXX11'] = False
            cmake.definitions['ENABLE_OPENCL'] = True
            cmake.definitions['ENABLE_OPENGL'] = False # Use the OpenCL packet processor, which is faster than the OpenGL packet processor.
            cmake.definitions['ENABLE_PROFILING'] = True
            cmake.definitions['ENABLE_TEGRAJPEG'] = False
            cmake.definitions['ENABLE_VAAPI'] = False
            cmake.configure(source_dir='../%s' % self.source_dir,
                            build_dir='.',
                            args=['-Wno-dev', '--no-warn-unused-cli'])
            cmake.build()
            self.run('install_name_tool -id @rpath/%s lib/%s' % (self.dylib_name, self.dylib_name))

    def package(self):
        self.copy('*.h', src='%s/include/libfreenect2' % self.source_dir, dst='include/libfreenect2')
        self.copy('*.h', src='%s/libfreenect2' % self.build_dir, dst='include/libfreenect2')
        self.copy('*.hpp', src='%s/include/libfreenect2' % self.source_dir, dst='include/libfreenect2')
        self.copy(self.dylib_name, src='%s/lib' % self.build_dir, dst='lib')

    def package_info(self):
        self.cpp_info.libs = ['freenect2.%s' % self.version]
