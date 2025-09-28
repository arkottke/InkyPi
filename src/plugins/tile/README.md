# Tile Layout Plugin for InkyPi

A powerful layout plugin that creates a customizable grid system to host multiple other plugins in tiles on your InkyPi display.

## Features

- **Flexible Grid Layout**: Choose from 2×2 up to 10×10 grid sizes
- **Multi-Plugin Support**: Host different plugins in each tile
- **Custom Tile Sizes**: Tiles can span multiple grid cells
- **Visual Configuration**: Interactive grid editor in settings
- **Border Control**: Show/hide grid borders with custom colors
- **Background Customization**: Set custom background colors
- **Plugin Independence**: Each tile runs its plugin independently
- **Error Handling**: Graceful fallback when plugins fail to load
- **Responsive Design**: Adapts to display dimensions and orientation

## How It Works

### Grid System
- Define a grid from 2×2 to 10×10 cells
- Each cell represents a portion of your display
- Total display area is divided evenly among grid cells

### Tile Placement
- Tiles can occupy one or multiple grid cells
- Tiles must form rectangular areas
- No overlap between tiles is allowed
- Empty grid cells remain as background

### Plugin Hosting
- Each tile can host any other InkyPi plugin
- Plugins render into their assigned tile area
- Plugin settings can be configured per tile
- Failed plugins show error placeholders

## Configuration Options

### Basic Settings
- **Grid Size**: Select from 2×2 to 10×10 grid layouts
- **Show Grid Borders**: Toggle visibility of grid lines
- **Border Color**: Customize grid border color (hex color picker)
- **Background Color**: Set background color for empty areas

### Tile Configuration
- **Interactive Grid Editor**: Click and drag to select areas
- **Add Tiles**: Select rectangular areas and assign plugins
- **Plugin Assignment**: Choose which plugin renders in each tile
- **Tile Management**: Edit or remove existing tiles

## Usage Instructions

### Setting Up Your Grid

1. **Choose Grid Size**: Select your desired grid dimensions (e.g., 4×4)
2. **Configure Appearance**: Set border and background colors
3. **Enable Borders**: Check "Show Grid Borders" if desired

### Adding Tiles

1. **Select Area**: Click cells in the grid preview to select a rectangular area
2. **Create Tile**: Click "Add Tile" button
3. **Assign Plugin**: Enter the plugin ID (e.g., "clock", "weather", "calendar")
4. **Confirm**: The tile appears in the grid and tiles list

### Managing Tiles

- **Edit**: Click "Edit" next to any tile to change its plugin
- **Remove**: Click "Remove" to delete a tile
- **Clear All**: Use "Clear All Tiles" to start over

## Available Plugins

The tile system can host any InkyPi plugin except itself (to prevent recursion):

- **clock** - Analog and digital clocks
- **weather** - Weather information display  
- **calendar** - Calendar events and schedules
- **schoolmenu** - School lunch menus
- **ai_text** - AI-generated text content
- **ai_image** - AI-generated images
- **apod** - Astronomy Picture of the Day
- **comic** - Comic strips
- **image_folder** - Local image gallery
- **image_upload** - Uploaded images
- **image_url** - Images from URLs
- **newspaper** - News headlines
- **screenshot** - Website screenshots
- **unsplash** - Unsplash photography
- **wpotd** - Wikipedia Picture of the Day

## Technical Details

### Grid Calculations
- Display dimensions are divided by grid size to get cell dimensions
- Each tile gets a portion of the display based on its grid cell allocation
- Plugins receive a device config with their tile's dimensions

### Plugin Integration
- Each tile creates an isolated plugin instance
- Plugin settings are passed through from tile configuration
- Generated images are resized to fit tile dimensions if needed
- Color mode conversion handled automatically (BW ↔ RGB)

### Error Handling
- Invalid plugin IDs show error placeholders
- Failed plugin loads display error messages
- Malformed tile configurations fall back to defaults
- JSON parsing errors are logged and handled gracefully

## Example Configurations

### Simple 2×2 Layout
```json
[
  {"x": 0, "y": 0, "width": 1, "height": 1, "plugin_id": "clock"},
  {"x": 1, "y": 0, "width": 1, "height": 1, "plugin_id": "weather"},
  {"x": 0, "y": 1, "width": 2, "height": 1, "plugin_id": "calendar"}
]
```

### Complex 4×4 Dashboard
```json
[
  {"x": 0, "y": 0, "width": 2, "height": 2, "plugin_id": "clock"},
  {"x": 2, "y": 0, "width": 2, "height": 1, "plugin_id": "weather"},
  {"x": 2, "y": 1, "width": 1, "height": 1, "plugin_id": "apod"},
  {"x": 3, "y": 1, "width": 1, "height": 1, "plugin_id": "comic"},
  {"x": 0, "y": 2, "width": 4, "height": 2, "plugin_id": "calendar"}
]
```

## Performance Considerations

- Each plugin renders independently, so processing time scales with number of tiles
- Large grids with many plugins may take longer to generate
- Consider plugin complexity when designing layouts
- Network-dependent plugins (weather, news) may affect overall render time

## Troubleshooting

### Common Issues

**Plugin Not Found Error**
- Ensure plugin ID is spelled correctly
- Check that the plugin is installed and enabled
- Verify plugin-info.json exists for the plugin

**Tile Overlap Error**
- Tiles cannot overlap - check grid positions
- Clear existing tiles and recreate if needed

**Rendering Issues**
- Check individual plugin settings and configuration
- Verify display dimensions are sufficient for chosen grid size
- Review logs for specific plugin errors

**Configuration Not Saving**
- Ensure tiles configuration JSON is valid
- Check browser console for JavaScript errors
- Verify form submission includes tilesConfig field