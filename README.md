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
3. Enter the service (master) password, which is needed to change output modes and setpoints (factory default is prefilled)

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
- **Numbers** – setpoints from the web interface temperature page: tank base temperature and
  seasonal S1/S2 targets, heating curve, night setback, curve shift and flow limits of TO1/TO2,
  fireplace, solar, pool and cooling thresholds.

The controller has no way to set a value directly, only the -/+ buttons of its web interface.
Setting a number logs in with the master password, presses the button as many times as needed,
reads the value back and saves it to the controller's permanent memory. When the controller
refuses to go further, the reached value is kept and an error is shown. Some limits follow other
settings: a minimum flow or switch-on temperature cannot cross its maximum or switch-off pair,
and S1 cannot go below the tank base temperature.

Example – return the SP1 coil to automatic mode:

```yaml
action: select.select_option
target:
  entity_id: select.iq_r23_sp1_mode
data:
  option: auto
```

Data is polled every 15 seconds.

## Dashboard card

The integration ships a Lovelace card, so nothing else has to be installed. After a restart, add
the **iQ R23** card from the card picker, or in YAML:

```yaml
type: custom:iqr23-card
device_id: 0123456789abcdef  # optional, the first iQ R23 device is used otherwise
title: Kotelna               # optional
show_controls: true          # optional, -/+ buttons for setpoints
```

The card shows the outdoor temperature, active faults, the storage tank, heating circuits and the
fireplace, solar, pool and cooling temperatures. Sections of disabled modules are left out.
Entities are found by the device, so renamed entity IDs keep working. The -/+ buttons collect
presses and send one change after a short pause, since each change logs in to the controller.

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
