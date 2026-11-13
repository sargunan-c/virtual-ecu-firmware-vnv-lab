# Virtual ECU Firmware Makefile
CC = gcc
CFLAGS = -std=c11 -Wall -Wextra -O2 -I firmware/include
SRC = firmware/src/ecu_diagnostics.c \
      firmware/src/ecu_sensors.c \
      firmware/src/ecu_actuators.c \
      firmware/src/ecu_state_machine.c \
      firmware/src/ecu_fault_injection.c \
      firmware/src/ecu_firmware.c

all: dll exe

dll:
	$(CC) $(CFLAGS) -DBUILDING_ECU_DLL -shared $(SRC) -o firmware/build/virtual_ecu.dll

exe:
	$(CC) $(CFLAGS) $(SRC) firmware/src/main.c -o firmware/build/virtual_ecu.exe

clean:
	rm -f firmware/build/*.dll firmware/build/*.exe firmware/build/*.o

