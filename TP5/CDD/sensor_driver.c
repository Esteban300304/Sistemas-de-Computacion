#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/types.h>
#include <linux/kdev_t.h>
#include <linux/fs.h>
#include <linux/device.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/gpio/consumer.h>
#include <linux/gpio/driver.h>
#include <linux/gpio/machine.h>
#include <linux/gpio.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Electro");
MODULE_DESCRIPTION("CDD - Sensor de dos señales via GPIO");

#define DEVICE_NAME "sensor_driver"
#define CLASS_NAME  "sensor_driver_class"
#define BUF_SIZE    32

/* GPIOs disponibles */
#define GPIO_SIGNAL_0  16
#define GPIO_SIGNAL_1  18

static dev_t        first;
static struct cdev  c_dev;
static struct class *cl;
static struct gpio_device *gpio_dev;
static struct gpio_chip *gpio_chip;

static int signal_select = 0;  /* 0=GPIO16, 1=GPIO18 */
static char data_buf[BUF_SIZE];
static struct gpio_desc *gpio_desc_0;
static struct gpio_desc *gpio_desc_1;

/* Lee el valor de un GPIO usando la API de descriptores del kernel */
static int read_gpio(int gpio_num)
{
    struct gpio_desc *desc;

    if (gpio_num == GPIO_SIGNAL_0)
        desc = gpio_desc_0;
    else if (gpio_num == GPIO_SIGNAL_1)
        desc = gpio_desc_1;
    else
        desc = NULL;

    if (!desc) {
        printk(KERN_WARNING "sensor_driver: GPIO%d no soportado\n", gpio_num);
        return -1;
    }

    return gpiod_get_value_cansleep(desc);
}

/* --- File operations --- */
static int my_open(struct inode *i, struct file *f)
{
    printk(KERN_INFO "sensor_driver: open()\n");
    return 0;
}

static int my_close(struct inode *i, struct file *f)
{
    printk(KERN_INFO "sensor_driver: close()\n");
    return 0;
}

static ssize_t my_read(struct file *f, char __user *buf, size_t len, loff_t *off)
{
    int gpio_num;
    int gpio_val;
    int data_len;

    if (*off > 0)
        return 0; /* EOF */

    gpio_num = (signal_select == 0) ? GPIO_SIGNAL_0 : GPIO_SIGNAL_1;
    gpio_val = read_gpio(gpio_num);

    if (gpio_val < 0)
        snprintf(data_buf, BUF_SIZE, "GPIO%d:error\n", gpio_num);
    else
        snprintf(data_buf, BUF_SIZE, "GPIO%d:%d\n", gpio_num, gpio_val);

    data_len = strlen(data_buf);

    if (len < data_len)
        return -EINVAL;

    if (copy_to_user(buf, data_buf, data_len) != 0)
        return -EFAULT;

    *off += data_len;

    printk(KERN_INFO "sensor_driver: read() → %s", data_buf);
    return data_len;
}

static ssize_t my_write(struct file *f, const char __user *buf,
                        size_t len, loff_t *off)
{