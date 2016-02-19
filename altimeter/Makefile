DEVTREE   = LOON-ALTIMETER
CAPEMGR   = /sys/devices/bone_capemgr.9/slots
CXXFLAGS += -std=c++11 -O0 -g

all: LOON-ALTIMETER-00A0.dtbo read

%.dtbo: %.dts
	dtc -O dtb -o $@ -b 0 -@ $<

install: all
	install -m 644 LOON-ALTIMETER-00A0.dtbo /lib/firmware
	install -m 644 LOON-ALTIMETER-00A0.dts  /lib/firmware
	grep -q ${DEVTREE} ${CAPEMGR} || echo ${DEVTREE} > ${CAPEMGR}

clean:
	rm -f *.dtbo *.pyc *.o read

LOON-ALTIMETER-00A0.dtbo: LOON-ALTIMETER-00A0.dts

read: read.cc gpio.h handle.h spidev.h
