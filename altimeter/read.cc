#include "gpio.h"
#include "spidev.h"

int main(int argc, char** argv) {
    gpio_helper gpio("/sys/devices/ocp.3/altimeter.15/status");

    // Select in the appropriate sensor
    if (argc > 1) {
        const int n = atoi(argv[1]);
        gpio["altimeter:sel2"].value(static_cast<bool>(n & 0x04));
        gpio["altimeter:sel1"].value(static_cast<bool>(n & 0x02));
        gpio["altimeter:sel0"].value(static_cast<bool>(n & 0x01));
        ::usleep(50000);
    }

    // Read the current configuration
    int num = 0;
    num |= gpio["altimeter:sel2"].value() ? 0x04 : 0;
    num |= gpio["altimeter:sel1"].value() ? 0x02 : 0;
    num |= gpio["altimeter:sel0"].value() ? 0x01 : 0;

    // Configure the ADC
    spidev adc(1, 0);
    adc.mode(3);
    const uint8_t gain_word1[] = { 0x10, 0x02 };
    adc.write(gain_word1, sizeof(gain_word1));
    const uint8_t gain_word2[] = { 0x01, 0x78 };
    adc.write(gain_word2, sizeof(gain_word2));
    ::usleep(50000);

    // Read the ADC
    const uint8_t data_word1[] = { 0x10, 0x01 };
    adc.write(data_word1, sizeof(data_word1));
    const uint8_t data_word2[] = { 0xEA, 0, 0, 0, 0, 0, 0, 0, 0 };
    uint8_t data[sizeof(data_word2)];
    adc.readwrite(data, data_word2, sizeof(data_word2));

    // Format the output
    const int32_t value = ((int8_t)data[1] << 16) | (data[2] << 8) | data[3];
    printf("%d,%d,%s\n", num, value,
        gpio["altimeter:temp_ok"].value() ? "true" : "false");
}
