# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-02-20

### Fixed
- Security validation to prevent scanner from escaping base_dir
- Reader text "Connected" translation to English

### Changed
- Improved reader layout with wider content area (100% width)
- Better typography with 1.9 line-height and 1.1rem font-size
- Larger heading sizes for better readability

### Added
- Export to HTML endpoint (`/api/export/html/{path}`) for printing/PDF
- Download markdown endpoint (`/api/export/markdown/{path}`)
- Export buttons in viewer (HTML and .md download)

## [1.0.2] - 2025-02-20

### Added
- MIT LICENSE file
- Link to LICENSE in README

## [1.0.1] - 2025-02-20

### Changed
- Removed redundant title from README (logo already shows name)
- Removed author section from README
- Easter egg texts translated to English

## [1.0.0] - 2025-02-20

### Added
- Initial release
- Auto-detection of markdown files
- Shinto-inspired theme with dark/light modes
- Real-time file watching with WebSocket
- Full-text search
- Inline editor with live preview
- HTML caching for performance
- Kitsune Mode easter eggs (optional via settings)
- Pip-installable package
