# iQ R23 Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for the iQ R23 heating controller made by iQ vytápění. It reads the
controller's local web interface and lets you monitor and control the heating system from Home Assistant.

> **Disclaimer:** This is an unofficial, community-developed integration. It is not affiliated with,
> endorsed by or supported by iQ vytápění s.r.o. "iQ vytápění", "iQ R23" and the related logos are
> trademarks of their respective owners and are used only to identify the supported device.
> Use at your own risk.

## Features

- **Temperatures** – outdoor, storage tank, heating circuits TO1/TO2, fireplace, solar, pool and cooling
- **Status** – heating coils, pumps, thermostat demands, low tariff and fault inputs
- **Output control** – switch every output between Auto, AutoR, On and Off
- **Setpoints** – tank, heating circuit, fireplace, solar, pool and cooling temperatures
- **Dashboard card** – bundled Lovelace card, no separate installation needed

## Setup

1. Install via HACS and restart Home Assistant
2. Add the **iQ R23** integration in Settings → Devices & Services
3. Enter the controller's IP address or hostname and the service (master) password
