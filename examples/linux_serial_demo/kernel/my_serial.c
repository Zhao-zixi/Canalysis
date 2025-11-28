#include <linux/module.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/kfifo.h>
#include <linux/slab.h>
#include "../common/serial_proto.h"

static dev_t devno;
static struct cdev my_cdev;
static struct class *my_class;
static struct device *my_device;
static struct kfifo rx_fifo;
static struct kfifo tx_fifo;
static struct serial_config current_cfg;
static u32_t rx_bytes;
static u32_t tx_bytes;

static ssize_t serial_send(const char *buf, size_t len) {
    unsigned int copied = kfifo_in(&tx_fifo, buf, len);
    kfifo_in(&rx_fifo, buf, copied);
    tx_bytes += copied;
    return copied;
}

static ssize_t serial_recv(char *buf, size_t len) {
    unsigned int copied = kfifo_out(&rx_fifo, buf, len);
    rx_bytes += copied;
    return copied;
}

static int serial_config(struct serial_config *cfg) {
    current_cfg = *cfg;
    return 0;
}

static int my_open(struct inode *inode, struct file *file) {
    return 0;
}

static int my_release(struct inode *inode, struct file *file) {
    return 0;
}

static ssize_t my_read(struct file *file, char __user *ubuf, size_t len, loff_t *off) {
    char *kbuf;
    ssize_t ret;
    if (len == 0) return 0;
    kbuf = kmalloc(len, GFP_KERNEL);
    if (!kbuf) return -ENOMEM;
    ret = serial_recv(kbuf, len);
    if (ret > 0) {
        if (copy_to_user(ubuf, kbuf, ret)) {
            kfree(kbuf);
            return -EFAULT;
        }
    }
    kfree(kbuf);
    return ret;
}

static ssize_t my_write(struct file *file, const char __user *ubuf, size_t len, loff_t *off) {
    char *kbuf;
    ssize_t ret;
    if (len == 0) return 0;
    kbuf = kmalloc(len, GFP_KERNEL);
    if (!kbuf) return -ENOMEM;
    if (copy_from_user(kbuf, ubuf, len)) {
        kfree(kbuf);
        return -EFAULT;
    }
    ret = serial_send(kbuf, len);
    kfree(kbuf);
    return ret;
}

static long my_ioctl(struct file *file, unsigned int cmd, unsigned long arg) {
    switch (cmd) {
        case MY_SERIAL_IOCTL_CONFIG: {
            struct serial_config cfg;
            if (copy_from_user(&cfg, (void __user *)arg, sizeof(cfg))) return -EFAULT;
            return serial_config(&cfg);
        }
        case MY_SERIAL_IOCTL_STATUS: {
            struct serial_status st;
            st.rx_bytes = rx_bytes;
            st.tx_bytes = tx_bytes;
            if (copy_to_user((void __user *)arg, &st, sizeof(st))) return -EFAULT;
            return 0;
        }
        default:
            return -EINVAL;
    }
}

static const struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = my_open,
    .release = my_release,
    .read = my_read,
    .write = my_write,
    .unlocked_ioctl = my_ioctl,
};

static int __init my_init(void) {
    int r;
    r = alloc_chrdev_region(&devno, 0, 1, "my_serial");
    if (r) return r;
    cdev_init(&my_cdev, &fops);
    r = cdev_add(&my_cdev, devno, 1);
    if (r) {
        unregister_chrdev_region(devno, 1);
        return r;
    }
    my_class = class_create(THIS_MODULE, "my_serial");
    if (IS_ERR(my_class)) {
        cdev_del(&my_cdev);
        unregister_chrdev_region(devno, 1);
        return PTR_ERR(my_class);
    }
    my_device = device_create(my_class, NULL, devno, NULL, "my_serial");
    if (IS_ERR(my_device)) {
        class_destroy(my_class);
        cdev_del(&my_cdev);
        unregister_chrdev_region(devno, 1);
        return PTR_ERR(my_device);
    }
    r = kfifo_alloc(&rx_fifo, 4096, GFP_KERNEL);
    if (r) {
        device_destroy(my_class, devno);
        class_destroy(my_class);
        cdev_del(&my_cdev);
        unregister_chrdev_region(devno, 1);
        return r;
    }
    r = kfifo_alloc(&tx_fifo, 4096, GFP_KERNEL);
    if (r) {
        kfifo_free(&rx_fifo);
        device_destroy(my_class, devno);
        class_destroy(my_class);
        cdev_del(&my_cdev);
        unregister_chrdev_region(devno, 1);
        return r;
    }
    rx_bytes = 0;
    tx_bytes = 0;
    current_cfg.baud = 115200;
    current_cfg.parity = 0;
    current_cfg.stop_bits = 1;
    return 0;
}

static void __exit my_exit(void) {
    kfifo_free(&rx_fifo);
    kfifo_free(&tx_fifo);
    device_destroy(my_class, devno);
    class_destroy(my_class);
    cdev_del(&my_cdev);
    unregister_chrdev_region(devno, 1);
}

module_init(my_init);
module_exit(my_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("demo");
MODULE_DESCRIPTION("my_serial");
