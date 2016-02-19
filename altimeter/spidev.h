#ifndef SPIDEV_WRAP_H
#define SPIDEV_WRAP_H
#include "handle.h"
#include <linux/spi/spidev.h>
#include <cstring>

class spidev {
public:
    spidev(unsigned bus, unsigned chip) : bpw_(8) {
        char spifile[64];
        snprintf(spifile, sizeof(spifile), "/dev/spidev%u.%u", bus, chip);
        spi_.open(spifile, O_RDWR);
    }

    int mode() const {
        uint8_t v = 0;
        spi_.ioctl(SPI_IOC_RD_MODE, &v);
        return v;
    }
    void mode(int m) {
        uint8_t v = static_cast<uint8_t>(m);
        spi_.ioctl(SPI_IOC_WR_MODE, &v);
    }

    void write(const void* buf, size_t size) { readwrite(nullptr, buf, size); }
    void read(void* buf, size_t size)        { readwrite(buf, nullptr, size); }

    void readwrite(void *rxbuf, const void* txbuf, size_t size) {
        spi_ioc_transfer tr;
        memset(&tr, 0, sizeof(tr));
        tr.tx_buf = reinterpret_cast<size_t>(txbuf);
        tr.rx_buf = reinterpret_cast<size_t>(rxbuf);
        tr.len = size;
        tr.speed_hz = 0;
        tr.bits_per_word = bpw_;
        tr.cs_change = 1;
        spi_.ioctl(SPI_IOC_MESSAGE(1), &tr);
    }

private:
    handle spi_;
    int bpw_;
};

#endif // SPIDEV_WRAP_H
