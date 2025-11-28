#ifndef SERIAL_USER_H
#define SERIAL_USER_H
#include "../common/serial_proto.h"
#include <stddef.h>
#include <sys/types.h>
typedef struct serial_handle serial_handle;
serial_handle* serial_open(const char* path);
void serial_close(serial_handle* h);
ssize_t serial_send(serial_handle* h, const void* buf, size_t len);
ssize_t serial_recv(serial_handle* h, void* buf, size_t len);
int serial_config(serial_handle* h, const struct serial_config* cfg);
int serial_get_status(serial_handle* h, struct serial_status* st);
#endif
