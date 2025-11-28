#ifndef SERIAL_PROTO_H
#define SERIAL_PROTO_H
#ifdef __KERNEL__
#include <linux/types.h>
#include <linux/ioctl.h>
typedef __u32 u32_t;
typedef __u8 u8_t;
#else
#include <stdint.h>
#include <sys/ioctl.h>
typedef uint32_t u32_t;
typedef uint8_t u8_t;
#endif

#define MY_SERIAL_IOC_MAGIC 'M'
struct serial_config { u32_t baud; u8_t parity; u8_t stop_bits; u8_t reserved[2]; };
struct serial_status { u32_t rx_bytes; u32_t tx_bytes; };
#define MY_SERIAL_IOCTL_CONFIG _IOW(MY_SERIAL_IOC_MAGIC, 1, struct serial_config)
#define MY_SERIAL_IOCTL_STATUS _IOR(MY_SERIAL_IOC_MAGIC, 2, struct serial_status)

#endif
