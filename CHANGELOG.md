# Changelog

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
