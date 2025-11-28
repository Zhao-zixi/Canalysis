CC = gcc
CFLAGS = -O2 -Wall

all: libserial_user.a example_app

libserial_user.a: libserial_user.o
	ar rcs $@ $^

libserial_user.o: libserial_user.c serial_user.h ../common/serial_proto.h
	$(CC) $(CFLAGS) -c libserial_user.c -o $@

example_app: example_app.o libserial_user.a
	$(CC) $(CFLAGS) -o $@ example_app.o libserial_user.a

example_app.o: example_app.c serial_user.h ../common/serial_proto.h
	$(CC) $(CFLAGS) -c example_app.c -o $@

clean:
	rm -f *.o *.a example_app
