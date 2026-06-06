#!/bin/sh

QEMU=qemu-system-aarch64

get_qemu_version() {
    "$QEMU" --version | perl -ne 'print $1 if /version (\S+)/'
}

check_version_at_least() {
    V="$( (echo "$1" ; get_qemu_version) | sort -V | head -1 )"
    test "$V" = "$1"
    return $?
}

# COMENTADO: Evitamos que te saque de la carpeta actual del repositorio
# cd "$HOME"

# Target root with kernel and dtbs
ROOTFS=rootfs

# No necesitamos buscar en un .zip, sabemos exactamente cómo se llama la imagen
IMGNAME="/home/esteban/Sistemas-de-Computacion/TP5/qemu-gpio-rpi/raspios_lite_armhf_latest.img"

# Port to forward ssh to
SSHPORT=50022
# Guest resources
MEMORY_MB=1024
SMP_CPUS=4
# Enable or disable GPIO management
ENABLEQTEST=true
#ENABLEQTEST=false
QTESTSOCKET="/tmp/qtest.sock"

echo "[ ] root image: $IMGNAME"

BOOTPARAMS=""
# Console and system prints
#BOOTPARAMS="$BOOTPARAMS kgdboc=ttyAMA0,115200"
#BOOTPARAMS="$BOOTPARAMS console=tty1 console=ttyAMA0,115200 console=ttyS1,115200"
BOOTPARAMS="$BOOTPARAMS console=ttyAMA0,115200 console=ttyS0,115200 console=tty1 kgdboc=ttyAMA0,115200"
BOOTPARAMS="$BOOTPARAMS earlyprintk"
BOOTPARAMS="$BOOTPARAMS loglevel=8"
# Root and fs
BOOTPARAMS="$BOOTPARAMS rw"
BOOTPARAMS="$BOOTPARAMS root=/dev/mmcblk0p2"
BOOTPARAMS="$BOOTPARAMS rootwait"
BOOTPARAMS="$BOOTPARAMS rootfstype=ext4"
BOOTPARAMS="$BOOTPARAMS systemd.watchdog_device=/dev/watchdog9"

NETPARAMS=""

if check_version_at_least "5.1.0"; then
    NETPARAMS="$NETPARAMS -device usb-net,bus=usb-bus.0,netdev=net0"
    NETPARAMS="$NETPARAMS -netdev user,id=net0,hostfwd=tcp::50022-:22"
fi

QTESTPARAMS=""
if $ENABLEQTEST; then
    QTESTPARAMS="$QTESTPARAMS -qtest unix:$QTESTSOCKET"
fi

# Creamos una variable de control separada para los logs
ENABLE_LOGS=false
LOGPARAMS=""
if $ENABLE_LOGS; then
    LOGPARAMS="$LOGPARAMS -D /tmp/qemu.log"
    LOGPARAMS="$LOGPARAMS -d guest_errors"
fi

SERIAL=""
SERIAL="$SERIAL -monitor unix:/tmp/monitor.sock,server,nowait"

"$QEMU"                                                       \
    $SERIAL                                                   \
    -M       raspi3b                                          \
    -m       "$MEMORY_MB"                                     \
    -smp     "$SMP_CPUS"                                      \
    -dtb "/home/esteban/Sistemas-de-Computacion/TP5/qemu-gpio-rpi/qemu-setup/$ROOTFS/bcm2710-rpi-3-b.dtb" \
    -kernel "/home/esteban/Sistemas-de-Computacion/TP5/qemu-gpio-rpi/qemu-setup/rootfs/kernel8.img" \
    -append  "$BOOTPARAMS"                                    \
    -drive   "file=$IMGNAME,if=sd,format=raw,index=0"         \
    $NETPARAMS                                                \
    $QTESTPARAMS                                              \
    $LOGPARAMS                                                \
    ;
