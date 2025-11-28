#include "serial_user.h"
#include <stdio.h>
#include <string.h>

int main() {
    serial_handle* h = serial_open("/dev/my_serial");
    if (!h) {
        printf("open failed\n");
        return 1;
    }
    struct serial_config cfg;
    cfg.baud = 115200;
    cfg.parity = 0;
    cfg.stop_bits = 1;
    serial_config(h, &cfg);
    const char *msg = "hello";
    char buf[64];
    serial_send(h, msg, strlen(msg));
    ssize_t n = serial_recv(h, buf, sizeof(buf));
    if (n > 0) {
        fwrite(buf, 1, n, stdout);
        printf("\n");
    }
    struct serial_status st;
    serial_get_status(h, &st);
    printf("rx=%u tx=%u\n", st.rx_bytes, st.tx_bytes);
    serial_close(h);
    return 0;
}
