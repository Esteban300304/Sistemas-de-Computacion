#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Equipo Electro");
MODULE_DESCRIPTION("Modulo basico para TP");

static int __init electro_init(void) {
    printk(KERN_INFO "Equipo Electro: Modulo cargado exitosamente.\n");
    return 0;
}

static void __exit electro_exit(void) {
    printk(KERN_INFO "Equipo Electro: Modulo descargado.\n");
}

module_init(electro_init);
module_exit(electro_exit);
