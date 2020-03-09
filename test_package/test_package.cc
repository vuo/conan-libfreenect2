#include <stdio.h>
#include <libfreenect2/libfreenect2.hpp>

int main()
{
	libfreenect2::Freenect2 *f = new libfreenect2::Freenect2;
	if (!f)
	{
		printf("Couldn't initialize the Freenect2 driver.\n");
		return -1;
	}

	printf("Successfully initialized the Freenect2 driver.  Detected %d currently-attached device(s).\n", f->enumerateDevices());

#ifndef linux
	libfreenect2::PacketPipeline *pipeline = new libfreenect2::OpenCLPacketPipeline(-1);
	if (!pipeline)
	{
		printf("Couldn't initialize the OpenCL pipeline.\n");
		return -1;
	}

	printf("Successfully initialized the OpenCL pipeline.\n");

	delete pipeline;
#endif

	delete f;

	return 0;
}
