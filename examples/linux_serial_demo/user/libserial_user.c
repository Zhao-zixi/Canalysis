#include "serial_user.h"
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>

struct serial_handle { int fd; };

serial_handle* serial_open(const char* path) {
    serial_handle* h = (serial_handle*)malloc(sizeof(serial_handle));
    if (!h) return NULL;
    int fd = open(path, O_RDWR);
    if (fd < 0) { free(h); return NULL; }
    h->fd = fd;
    return h;
}

void serial_close(serial_handle* h) {
    if (!h) return;
    if (h->fd >= 0) close(h->fd);
    free(h);
}

ssize_t serial_send(serial_handle* h, const void* buf, size_t len) {
    if (!h) return -1;
    return write(h->fd, buf, len);
}

ssize_t serial_recv(serial_handle* h, void* buf, size_t len) {
    if (!h) return -1;
    return read(h->fd, buf, len);
}

int serial_config(serial_handle* h, const struct serial_config* cfg) {
    if (!h) return -1;
    return ioctl(h->fd, MY_SERIAL_IOCTL_CONFIG, cfg);
}

int serial_get_status(serial_handle* h, struct serial_status* st) {
    if (!h) return -1;
    return ioctl(h->fd, MY_SERIAL_IOCTL_STATUS, st);
}
