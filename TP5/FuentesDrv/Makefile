DRV ?= 3

obj-m := Drv$(DRV).o

KDIR  := /lib/modules/$(shell uname -r)/build
BUILD := $(PWD)/build

all:
	mkdir -p $(BUILD)
	make -C $(KDIR) M=$(PWD) modules
	find $(PWD) -maxdepth 1 -name "*.o" -o -name "*.ko" -o -name "*.mod" -o -name "*.mod.c" -o -name "*.order" -o -name "*.symvers" -o -name "*.cmd" | xargs -I{} mv -f {} $(BUILD)/ 2>/dev/null || true
	find $(PWD) -maxdepth 1 -name ".*.cmd" -o -name ".*.o" | xargs -I{} mv -f {} $(BUILD)/ 2>/dev/null || true

clean:
	rm -rf $(BUILD)
	make -C $(KDIR) M=$(PWD) clean

load:
	sudo insmod $(BUILD)/Drv$(DRV).ko

unload:
	sudo rmmod Drv$(DRV)

log:
	sudo dmesg | tail -10

logclear:
	sudo dmesg -C