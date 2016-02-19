#ifndef GPIO_H
#define GPIO_H
#include "handle.h"
#include <map>
#include <string>

class gpio {
public:
    explicit gpio(int id) : id_(id) {}

    bool value() const {
        char filename[64];
        snprintf(filename, sizeof(filename),
            "/sys/devices/virtual/gpio/gpio%d/value", id_);
        stdio_handle handle(filename, "r");
        int result = 0;
        handle.scanf("%d", &result);
        return static_cast<bool>(result);
    }

    void value(bool v) {
        char filename[64];
        snprintf(filename, sizeof(filename),
            "/sys/devices/virtual/gpio/gpio%d/value", id_);
        stdio_handle handle(filename, "w");
        handle.printf("%d\n", static_cast<int>(v));
    }
private:
    int id_;
};

class gpio_helper {
public:
    gpio_helper(const char *name) {
        stdio_handle file(name, "rt");
        int pin;
        char gpioname[64];
        while (sscanf(file.readline().c_str(), "%*u%64s%u",
                gpioname, &pin) >= 2) {
            gpio_.insert(std::make_pair(gpioname, pin));
        }
    }

    gpio operator[](const char *name) const {
        return gpio(gpio_.at(name));
    }

    gpio operator[](const std::string& name) const {
        return gpio(gpio_.at(name));
    }
private:
    std::map<std::string, int> gpio_;
};

#endif // GPIO_H
