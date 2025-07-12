# iQ R23 for Home Assistant

This is a Home Assistant integration for the iQ R23 heating controller.

## Installation

### HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Install the integration through HACS
3. Restart Home Assistant
4. Add the integration through the UI

### Manual Installation

1. Copy the `custom_components/iqr23` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the UI

## Configuration

The integration can be configured through the Home Assistant UI:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "iQ R23"
4. Enter the IP address or hostname of your iQ R23 controller

## Features

- Temperature sensors for various zones
- Binary sensors for system status
- Switch controls for heating outputs
- Real-time data polling from the controller

## Supported Entities

### Sensors
- Outdoor temperature
- Water tank temperatures (upper, middle, lower)
- Floor heating temperatures
- Fireplace temperature
- Solar panel temperature

### Binary Sensors
- System pressure status
- Heating element status
- Circulation pump status
- Low tariff status

### Switches
- Various digital outputs (SP1, SP2, OVR, etc.)
