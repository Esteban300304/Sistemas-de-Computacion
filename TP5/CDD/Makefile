obj-m := sensor_driver.o

KDIR  := /lib/modules/$(shell uname -r)/build
BUILD := $(CURDIR)/build

all:
	mkdir -p "$(BUILD)"
	$(MAKE) -C "$(KDIR)" M="$(CURDIR)" modules
	find "$(CURDIR)" -maxdepth 1 \( -name "*.o" -o -name "*.ko" -o -name "*.mod*" -o -name "*.order" -o -name "*.symvers" -o -name "*.cmd" \) -exec mv -f {} "$(BUILD)/" \; 2>/dev/null || true
	find "$(CURDIR)" -maxdepth 1 -name ".*.cmd" -exec mv -f {} "$(BUILD)/" \; 2>/dev/null || true

clean:
	rm -rf "$(BUILD)"
	$(MAKE) -C "$(KDIR)" M="$(CURDIR)" clean


load: all
	sudo rmmod sensor_driver 2>/dev/null || true
	sudo insmod "$(BUILD)/sensor_driver.ko"
	sudo chmod 666 /dev/sensor_driver

unload:
	sudo rmmod sensor_driver

log:
	sudo dmesg | tail -15
