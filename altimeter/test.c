#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>
#include <linux/i2c-dev.h>

int main() {
	const uint8_t uagain[] = { 0x10, 0x02 };
	const uint8_t wrgain[] = { 0x01, 0x78 };
	const uint8_t uadat[]  = { 0x10, 0x01 };
	const uint8_t wrdat[9] = { 0xEA, 0 };
	uint8_t data[sizeof(wrdat)];

	struct spi_ioc_transfer tr[4];
	FILE *f;
	int  ch, i, j, spi, mux;
	uint8_t muxport;

	spi = open("/dev/spidev1.0", O_RDWR);
	muxport = SPI_MODE_3;
	ioctl(spi, SPI_IOC_WR_MODE, &muxport);

	mux = open("/dev/i2c-1", O_RDWR);
	i = 0x70;
	ioctl(mux, I2C_SLAVE, i);

	memset(tr, 0, sizeof(tr));
	for (i = 0; i < 4; ++i) {
		tr[i].rx_buf = 0;
		tr[i].delay_usecs = 0;
		tr[i].speed_hz = 500000;
		tr[i].bits_per_word = 8;
		tr[i].cs_change = 1;
	}
	tr[0].tx_buf = uagain;
	tr[0].len = sizeof(uagain);
	tr[1].tx_buf = wrgain;
	tr[1].len = sizeof(wrgain);
	tr[2].tx_buf = uadat;
	tr[2].len = sizeof(uadat);
	tr[3].tx_buf = wrdat;
	tr[3].rx_buf = data;
	tr[3].len = sizeof(wrdat);

	for (i = 0; i < 8; ++i) {
		f = fopen("/sys/devices/virtual/gpio/gpio30/value", "w");
		fputs((i & 1) ? "1\n" : "0\n", f);
		fclose(f);
		f = fopen("/sys/devices/virtual/gpio/gpio31/value", "w");
		fputs((i & 2) ? "1\n" : "0\n", f);
		fclose(f);
		f = fopen("/sys/devices/virtual/gpio/gpio48/value", "w");
		fputs((i & 4) ? "1\n" : "0\n", f);
		fclose(f);

		muxport = (uint8_t)(1U << i);
		write(mux, &muxport, 1);
		
		f = fopen("/sys/bus/i2c/devices/1-0050/eeprom", "r");
		errno = 0;
		ch = fgetc(f);
		fclose(f);
		printf("CH%d: %s\n", i, strerror(errno));

		f = fopen("/sys/devices/virtual/gpio/gpio51/value", "r");
		ch = fgetc(f);
		fclose(f);
		printf("CH%d: %s\n", i, (ch == '1') ? "TEMP_OK" : "Not at temp");

		memset(data, 0x55, sizeof(data));
		if (ioctl(spi, SPI_IOC_MESSAGE(3), &tr[0]) < 0)
			perror("ioctl[0]");
		if (ioctl(spi, SPI_IOC_MESSAGE(1), &tr[3]) < 0)
			perror("ioctl[3]");
		printf("CH%d: ", i);
		for (j = 0; j < sizeof(data); ++j)
			printf("%.2X ", data[j]);
		j = ((int8_t)data[1] << 16) | (data[2] << 8) | data[3];
		printf("(%d)\n", j);
	}
}
