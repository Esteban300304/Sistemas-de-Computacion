#!/bin/sh
TARGET=https://downloads.raspberrypi.org/raspios_lite_arm64_latest
DISK="sd.img"
BOOTFS=rootfs
SIZE=256
SIZEUNIT=M
TMPMOUNT=tmpmnt

setup_dependencies() {
    sudo apt update
    sudo apt install -y qemu-system-arm
    # Cambiamos p7zip-full por xz-utils, la herramienta estándar para archivos .xz
    sudo apt install -y xz-utils 
}

download_pi_os() {
    TARGET="$1"
    ARCHIVE="raspios_lite_arm64_latest.img.xz"
    IMGNAME="raspios_lite_arm64_latest.img"
    
    # Descargamos el archivo con la extensión correcta
    wget -O "$ARCHIVE" -c "$TARGET" >&2
    
    # Descomprimimos con xz-utils conservando el comprimido original (-k) por si acaso
    if [ ! -f "$IMGNAME" ]; then
        unxz -k "$ARCHIVE" > /dev/null
    fi
    
    # Retornamos el nombre de la imagen lista para usar
    echo "$IMGNAME"
}

get_files() {
    BOOTFS="$1"
    TMPMOUNT="$2"
    IMGNAME="$3"
    
    echo "Preparando directorios..."
    mkdir -p "$BOOTFS"
    mkdir -p "$TMPMOUNT"

    echo "Montando imagen leyendo la tabla de particiones..."
    # -P escanea las particiones y --show nos devuelve qué /dev/loop asignó
    DEVNAME=$(sudo losetup -P -f --show "$IMGNAME")
    
    # Al usar -P, Linux crea sub-dispositivos para cada partición. 
    # 'p1' es la partición de arranque (bootfs)
    sudo mount "${DEVNAME}p1" "$TMPMOUNT"
    
    echo "Extrayendo archivos de arranque..."
    sudo cp -rav "$TMPMOUNT"/* "$BOOTFS"
    sudo chown -R "$USER:$USER" "$BOOTFS"
    
    echo "Desmontando y limpiando..."
    sudo umount "$TMPMOUNT"
    sudo losetup -d "$DEVNAME"

    cp -rav "$BOOTFS" "$BOOTFS.orig"
}

resize_img() {
    IMGNAME="$1"
    SIZE="$2"
    # Quitamos el --shrink para no volver a romper el sistema de archivos
    qemu-img resize -f raw "$IMGNAME" "$SIZE"
}

cd "$HOME"

setup_dependencies
IMGNAME="$(download_pi_os "$TARGET")"
get_files "$BOOTFS" "$TMPMOUNT" "$IMGNAME"
# Cambiamos 2G por 4G para expandir la tarjeta SD virtual de forma segura
resize_img "$IMGNAME" 4G
