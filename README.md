# iQ R23 for Home Assistant

This is a Home Assistant integration for the [iQ R23](https://www.iqvytapeni.cz/) heating controller
made by iQ vytápění s.r.o. for iQ TAT storage tanks
([user manual](https://www.iqvytapeni.cz/files/uploads/ke%20stazeni/manual_iQ_R23_2016_05_17.pdf), Czech).

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

1. Go to Settings → Devices & Services → Add Integration → **iQ R23**
2. Enter the IP address or hostname of the controller
3. Enter the service (master) password, which is needed to change output modes (factory default is prefilled)

The address and password can be changed later via **Reconfigure**.

The controller is universal, so the integration detects which modules are installed (storage tank,
heating circuits TO1/TO2, fireplace, solar, cooling, pool) from connected temperature sensors.
The selection can be changed in the integration **Options**; entities of other modules are not created.

## Entities

- **Sensors** – outdoor temperature (current, 24h min/max/mean), tank temperatures and targets,
  heating circuits TO1/TO2 (temperature, target, mixing valve), fireplace, solar collector,
  SP1/SP2 heating time counters, cooling and pool temperatures.
- **Binary sensors** – heating coils, pumps, thermostat demands, setback, low tariff, backup power,
  problem sensors (safety thermostat, pressure, overcurrent) and the actual state of every output.
  Digital inputs (DI) are available as diagnostic entities, disabled by default.
- **Selects** – operating mode of each output: `Auto`, `AutoR` (reverse auto), `On`, `Off`.

Example – return the SP1 coil to automatic mode:

```yaml
action: select.select_option
target:
  entity_id: select.iq_r23_sp1_mode
data:
  option: auto
```

Data is polled every 15 seconds.

## Upgrading from 1.x

Existing configuration is migrated automatically and entity IDs, custom names and history are kept.
Output switches are replaced by selects; a repair notice lists the removed switches so automations
and dashboards using them can be updated.

## Requirements

- Home Assistant 2025.2.0 or newer
- iQ R23 controller reachable over the network

## Troubleshooting

If you encounter issues:

1. Verify the IP address/hostname of your iQ R23 controller
2. Ensure the controller is accessible from your Home Assistant instance
3. Check the Home Assistant logs for any error messages
4. Restart Home Assistant after installation

## Support

For issues and feature requests, please use the [GitHub repository](https://github.com/filipek92/iqr23/issues).

## License

This integration is released under the MIT License.
