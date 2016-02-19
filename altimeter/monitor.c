#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <math.h>
#include <linux/spi/spidev.h>
#include <linux/i2c-dev.h>

int main() {
	const uint8_t uadat[]  = { 0x10, 0x01 };
	const uint8_t wrdat[9] = { 0xEA, 0 };
	uint8_t data[sizeof(wrdat)];

	struct spi_ioc_transfer tr[2];
	FILE *f;
	int  ch, i, j, spi, mux;
	uint8_t muxport;
	const int N = (2 << 10);

	int32_t x;
	double sumX, sumX2;

	spi = open("/dev/spidev1.0", O_RDWR);
	muxport = SPI_MODE_3;
	ioctl(spi, SPI_IOC_WR_MODE, &muxport);

	memset(tr, 0, sizeof(tr));
	for (i = 0; i < 2; ++i) {
		tr[i].rx_buf = 0;
		tr[i].delay_usecs = 0;
		tr[i].speed_hz = 500000;
		tr[i].bits_per_word = 8;
		tr[i].cs_change = 1;
	}
	tr[0].tx_buf = uadat;
	tr[0].len = sizeof(uadat);
	tr[1].tx_buf = wrdat;
	tr[1].rx_buf = data;
	tr[1].len = sizeof(wrdat);

	f = fopen("/sys/devices/virtual/gpio/gpio30/value", "w");
	fputs("1\n", f);
	fclose(f);
	f = fopen("/sys/devices/virtual/gpio/gpio31/value", "w");
	fputs("1\n", f);
	fclose(f);
	f = fopen("/sys/devices/virtual/gpio/gpio48/value", "w");
	fputs("1\n", f);
	fclose(f);

	for (;;) {
		sumX2 = sumX = 0;
		for (i = 0; i < N; ++i) {
			usleep(1000);
			if (ioctl(spi, SPI_IOC_MESSAGE(2), &tr[0]) < 0) {
				perror("ioctl");
			}

			x = ((int8_t)data[1] << 16) | (data[2] << 8) | data[3];
			sumX += x;
			sumX2 += pow(x, 2);
		}

		printf("<x> = %f, sx = %f\n",
						sumX / N,
						sqrt(sumX2/N - pow(sumX/N, 2)));
	}
}
