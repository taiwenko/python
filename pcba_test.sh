#!/usr/bin/env bash

PS_PATH="/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A703U53P-if00-port0"
CELL_LOAD_PATH="/dev/serial/by-path/pci-0000:00:1d.0-usb-0:1.4.7.2:1.0-port0"
EXT_LOAD_PATH="/dev/serial/by-path/pci-0000:00:1d.0-usb-0:1.4.7.1:1.0-port0"

MAJOR_TOM="$HOME/major-tom-release-avionics-42.0-tip1"

cd "$MAJOR_TOM"
workflow/battery_blade_pcba.py --outgoing \
        --battery-power-supply-path "${PS_PATH}" \
        --battery-cell-load-path "${CELL_LOAD_PATH}" \
	--battery-external-load-path "${EXT_LOAD_PATH}"
