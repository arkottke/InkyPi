# School Menu Plugin for InkyPi

A plugin that displays school lunch menu information on your InkyPi e-ink display with support for custom URL parsing and multi-day menu display.

## Features

- **Multi-day Display**: Show 1-7 days of menu items starting from today
- **Custom URL Support**: Parse menu data from any web URL  
- **Flexible Layout**: Adapts to single or multi-day display formats
- **Customizable Title**: Set your own display title
- **Optional Date Display**: Show/hide date information
- **Automatic Fallback**: Uses mock data if URL parsing fails
- **Clean Layout**: Organized with bullet points and day headers
- **Automatic Refresh Timestamp**: Shows when data was last updated
- **Multi-display Support**: Works with both black & white and color displays

## Files Structure

```
schoolmenu/
├── plugin-info.json      # Plugin metadata
├── schoolmenu.py         # Main plugin class
├── lunch_menu_service.py # Service for getting menu data
├── settings.html         # Plugin settings form
├── icon.png             # Plugin icon
└── README.md            # This file
```

## Configuration Options

The plugin provides the following settings:

- **Menu URL**: Enter a URL where menu data can be found (optional - uses mock data if empty)
- **Number of Days**: Display 1-7 days of menu data (1 Day, 2 Days, 3 Days, 4 Days, 5 Days (Work Week), 6 Days, 7 Days (Full Week))
- **Custom Title**: Set a custom title for the display (default: "School Lunch Menu")
- **Show Date**: Toggle whether to display the date (for single day) or day headers (for multi-day)
- **Show Refresh Time**: Toggle whether to display when the data was last refreshed

## URL Integration

### Current Implementation
- The plugin accepts any URL in the Menu URL field
- Currently falls back to mock data with a warning (URL parsing not yet implemented)
- Ready for extension to parse actual menu data from web sources

### Future Extensions
To integrate with a real school menu system:

1. **Extend `_fetch_menu_from_url()` method** in `lunch_menu_service.py`
2. **Add parsing logic** for your specific menu format (HTML, JSON, CSV, etc.)
3. **Handle different URL formats** (direct data URLs, web pages, APIs)
4. **Add error handling** for network issues and parsing failures

### Example Integration Ideas
- Parse HTML tables from school websites
- Fetch JSON data from school APIs  
- Import CSV files from nutrition services
- Scrape PDF menu documents
- **Custom Title**: Set a custom title for the display (default: "School Lunch Menu")
- **Show Date**: Toggle whether to display the date
- **Show Refresh Time**: Toggle whether to display when the data was last refreshed

## Mock Data

Currently, the plugin uses mock data for demonstration. The `LunchMenuService` includes sample menus for several dates in September/October 2025. When no URL is provided or URL fetching fails, the plugin automatically generates default menu items for the requested number of days.

## Layout Design

### Single Day Display
- Centered title with accent color
- Full date display (if enabled)
- Horizontal separator line  
- Bullet-pointed menu items
- Bottom refresh timestamp

### Multi-Day Display  
- Centered title with accent color
- Day headers (Today, Tomorrow, or day names)
- Compact date format (MM/DD) in headers if enabled
- Indented bullet-pointed menu items for each day
- Automatic space management with truncation
- Bottom refresh timestamp

The layout automatically adjusts to available space and truncates long content with indicators showing remaining items or days.

## Installation

The plugin is ready to use once the files are placed in the `src/plugins/schoolmenu/` directory of your InkyPi installation. The plugin will automatically appear in the InkyPi web interface.