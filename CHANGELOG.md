# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.3.3] - 2026-11-03

### Changed
- Test fixtures and helper scripts no longer refer to a particular installation; the fetch scripts
  require the controller address as an argument.
- README states that the integration is unofficial and not affiliated with iQ vytápění.

## [2.3.2] - 2026-11-03

### Added
- Integration icon and logo (iQ vytápění brand, light and dark variants) shipped in `brand/`,
  shown in the Home Assistant integration settings from 2026.3.

## [2.3.1] - 2026-10-31

### Changed
- The fireplace and solar icons on the card are only coloured while their pump is running; the solar
  tile also shows the running pump.

## [2.3.0] - 2026-10-25

### Added
- Lovelace card `custom:iqr23-card` bundled with the integration, no separate installation needed:
  outdoor temperature, fault banner, storage tank with heating state, heating circuits with pump,
  demand, setback and mixing valve, fireplace/solar/pool/cooling tiles and -/+ buttons for the tank
  base temperature and curve shifts. Presses are collected and sent as one change.

## [2.2.1] - 2026-10-25

### Changed
- Setpoint numbers tuned once at commissioning (seasonal S1/S2, heating curve, setback, flow limits,
  fireplace, solar, cooling) are configuration entities; tank base temperature, curve shifts and
  pool temperatures stay as controls.

## [2.2.0] - 2026-10-25

### Added
- Setpoint numbers: tank base temperature and seasonal S1/S2 targets, heating circuit TO1/TO2 curve,
  night setback, curve shift and flow limits, fireplace start temperature and hysteresis, solar
  temperature difference, pool and cooling on/off temperatures. The controller only offers -/+ buttons,
  so the integration presses them until the value is reached, verifies it and saves it.

## [2.1.0] - 2026-10-25

### Changed
- Entity keys (unique ID suffixes) were unified to snake_case, e.g. `watertankUpper` → `tank_upper`,
  `lowerFloorMixing` → `circuit_1_mixing`, `SP1_mode` → `output_sp1_mode`. Existing entries are migrated
  automatically; entity IDs, custom names and history are kept.
- The firmware version is stored as `firmware_version` in the config entry.
- The device manufacturer is `iQ vytápění` (was `IQ Topeni`).

## [2.0.2] - 2026-10-25

### Added
- Devices that no longer belong to the controller can be removed from the device page.

## [2.0.1] - 2026-10-25

### Fixed
- Releases before 1.1.2 registered the device with an empty identifier; the migration left it
  orphaned and created a second device.

## [2.0.0] - 2026-10-25

### Breaking
- Output switches were removed. Each output (SP1, SP2, OVR, KRB, SOL, TVC, TO1, TO2, TCC, T/C, H/D, STO) now has
  a mode select (`Auto` / `AutoR` / `On` / `Off`) and a binary sensor with the actual relay state.
  Turning a switch off used to leave the output in manual `Off` with no way back to `Auto`.
- The SOL output state (`binary_sensor.*_solarcirculation`) is now the `SOL output` binary sensor; the entity ID is kept.
- Minimum Home Assistant version is 2025.2.

### Changed
- Rewritten on top of `DataUpdateCoordinator`: one poll every 15 s instead of one per entity,
  short outages are bridged with the last known state.
- Shared HTTP session, typed client errors, writes hold a lock over the whole login → button → save → logout sequence.
- Entity names are translated (cs/en), temperatures have `measurement` state class, heating time counters
  are `duration` / `total_increasing`.
- Installed modules (tank, circuits TO1/TO2, fireplace, solar, cooling, pool) are detected from connected
  sensors and can be changed in the integration options; entities of other modules are not created.
- The master password is configurable; reconfiguration flow and diagnostics were added.
- Existing entries are migrated automatically, entity IDs, custom names and history are kept.

### Fixed
- The system pressure sensor always reported OK.
- A protection input disabled in the controller (yellow on the web UI) is no longer reported as a problem.
- Digital input sensors (DI ...) were always unavailable; their data file `data_n_tix.xml` is now polled.
  They are diagnostic entities disabled by default.
- Disconnected temperature sensors reported `NaN` instead of unknown.

## [1.2.2] - 2025-07-12

### Added
- HACS metadata, MIT license and a version management script.

## [1.1.2] - 2025-01-12

### Changed
- Replaced `requests` with `aiohttp` for better async compatibility
- Improved device info with proper identifiers, manufacturer, model, and software version
- Enhanced error handling and logging throughout the integration
- Standardized entity naming and unique IDs across all platforms
- Updated translations to remove unused fields
- Added proper timeout handling for HTTP requests
- Improved async context management

### Fixed
- Fixed inconsistent device identifiers across entities
- Fixed missing unique_id prefix in binary sensors
- Fixed deprecated warning messages in logs
- Fixed missing manufacturer and model information in device registry
- Fixed potential connection leaks with proper session management

### Added
- Better error logging for debugging purposes
- Comprehensive README with installation and configuration instructions
- Version tracking file
- Proper async discovery method with error handling

[Unreleased]: https://github.com/filipek92/iqr23/compare/v2.3.3...HEAD
[2.3.3]: https://github.com/filipek92/iqr23/compare/v2.3.2...v2.3.3
[2.3.2]: https://github.com/filipek92/iqr23/compare/v2.3.1...v2.3.2
[2.3.1]: https://github.com/filipek92/iqr23/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/filipek92/iqr23/compare/v2.2.1...v2.3.0
[2.2.1]: https://github.com/filipek92/iqr23/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/filipek92/iqr23/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/filipek92/iqr23/compare/v2.0.2...v2.1.0
[2.0.2]: https://github.com/filipek92/iqr23/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/filipek92/iqr23/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/filipek92/iqr23/compare/v1.2.2...v2.0.0
[1.2.2]: https://github.com/filipek92/iqr23/releases/tag/v1.2.2
