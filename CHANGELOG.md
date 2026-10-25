# Changelog

## [2.0.0] - Unreleased

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
