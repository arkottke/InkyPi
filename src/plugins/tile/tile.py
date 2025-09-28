"""
Tile Plugin for InkyPi
Creates a grid-based layout that can host other plugins in tiles
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from plugins.base_plugin.base_plugin import BasePlugin
from plugins.plugin_registry import get_plugin_instance
from utils.app_utils import get_font

logger = logging.getLogger(__name__)

# Grid size options
GRID_SIZES = {
    "2x2": (2, 2),
    "3x3": (3, 3),
    "4x4": (4, 4),
    "5x5": (5, 5),
    "6x6": (6, 6),
    "7x7": (7, 7),
    "8x8": (8, 8),
    "9x9": (9, 9),
    "10x10": (10, 10),
}


class TileConfig:
    """Configuration for a single tile"""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        plugin_id: str,
        plugin_settings: Optional[Dict[str, Any]] = None,
    ):
        self.x = x  # Grid position X
        self.y = y  # Grid position Y
        self.width = width  # Tile width in grid units
        self.height = height  # Tile height in grid units
        self.plugin_id = plugin_id  # ID of plugin to render in this tile
        self.plugin_settings = plugin_settings if plugin_settings is not None else {}

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "plugin_id": self.plugin_id,
            "plugin_settings": self.plugin_settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 1),
            height=data.get("height", 1),
            plugin_id=data.get("plugin_id", ""),
            plugin_settings=data.get("plugin_settings", {}),
        )


class TilePlugin(BasePlugin):
    """Plugin to create a grid-based layout hosting other plugins"""

    def __init__(self, config, **dependencies):
        super().__init__(config, **dependencies)

    def generate_settings_template(self):
        """Generate settings template parameters"""
        template_params = super().generate_settings_template()
        template_params["style_settings"] = "True"
        return template_params

    def generate_image(self, settings, device_config):
        """Generate the tile layout image"""
        try:
            # Get settings
            grid_size = settings.get("gridSize", "4x4")
            show_borders = settings.get("showBorders", True)
            border_color = settings.get("borderColor", "#cccccc")
            background_color = settings.get("backgroundColor", "#ffffff")

            # Parse tile configurations
            tiles_config = settings.get("tilesConfig", "[]")
            if isinstance(tiles_config, str):
                try:
                    tiles_data = json.loads(tiles_config)
                except json.JSONDecodeError:
                    logger.error("Invalid tiles configuration JSON")
                    tiles_data = []
            else:
                tiles_data = tiles_config

            # Convert to TileConfig objects
            tiles = [TileConfig.from_dict(tile_data) for tile_data in tiles_data]

            # Get device configuration
            dimensions = device_config.get_resolution()
            if device_config.get_config("orientation") == "vertical":
                dimensions = dimensions[::-1]

            width, height = dimensions

            # Get grid dimensions
            grid_cols, grid_rows = GRID_SIZES.get(grid_size, (4, 4))

            # Create main image
            if device_config.get_config("color") == "bw":
                img = Image.new("1", (width, height), 1)  # White background
                border_color_pil = 0  # Black borders for BW
            else:
                img = Image.new("RGB", (width, height), background_color)
                border_color_pil = self._hex_to_rgb(border_color)

            draw = ImageDraw.Draw(img)

            # Calculate tile dimensions
            tile_width = width // grid_cols
            tile_height = height // grid_rows

            # Draw grid borders if enabled
            if show_borders:
                self._draw_grid_borders(
                    draw, width, height, grid_cols, grid_rows, border_color_pil
                )

            # Create and place tiles
            for tile in tiles:
                try:
                    self._render_tile(img, tile, tile_width, tile_height, device_config)
                except Exception as e:
                    logger.error(
                        f"Error rendering tile with plugin '{tile.plugin_id}': {e}"
                    )
                    # Draw error placeholder
                    self._draw_error_tile(draw, tile, tile_width, tile_height, str(e))

            logger.info("Tile layout image generated successfully")
            return img

        except Exception as e:
            logger.error(f"Error generating tile layout image: {str(e)}")
            raise RuntimeError(f"Failed to generate tile layout image: {str(e)}")

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            return (
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
            )
        return (255, 255, 255)  # Default to white

    def _draw_grid_borders(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        grid_cols: int,
        grid_rows: int,
        border_color,
    ):
        """Draw grid borders"""
        tile_width = width // grid_cols
        tile_height = height // grid_rows

        # Draw vertical lines
        for col in range(1, grid_cols):
            x = col * tile_width
            draw.line([(x, 0), (x, height)], fill=border_color, width=1)

        # Draw horizontal lines
        for row in range(1, grid_rows):
            y = row * tile_height
            draw.line([(0, y), (width, y)], fill=border_color, width=1)

    def _render_tile(
        self,
        main_img: Image.Image,
        tile: TileConfig,
        tile_width: int,
        tile_height: int,
        device_config,
    ):
        """Render a single tile with its plugin"""

        # Calculate tile position and size
        tile_x = tile.x * tile_width
        tile_y = tile.y * tile_height
        tile_w = tile.width * tile_width
        tile_h = tile.height * tile_height

        # Create a device config for this tile
        tile_device_config = self._create_tile_device_config(
            device_config, (tile_w, tile_h)
        )

        # Get the plugin for this tile
        plugin_config = {
            "id": tile.plugin_id,
            "class": self._get_plugin_class_name(tile.plugin_id),
        }

        try:
            plugin_instance = get_plugin_instance(plugin_config)
            if plugin_instance:
                # Generate the plugin image
                plugin_img = plugin_instance.generate_image(
                    tile.plugin_settings, tile_device_config
                )

                # Resize plugin image to fit tile if necessary
                if plugin_img.size != (tile_w, tile_h):
                    plugin_img = plugin_img.resize(
                        (tile_w, tile_h), Image.Resampling.LANCZOS
                    )

                # Paste the plugin image onto the main image
                if main_img.mode == "1" and plugin_img.mode != "1":
                    # Convert color image to BW for BW displays
                    plugin_img = plugin_img.convert("1")
                elif main_img.mode == "RGB" and plugin_img.mode == "1":
                    # Convert BW image to RGB for color displays
                    plugin_img = plugin_img.convert("RGB")

                main_img.paste(plugin_img, (tile_x, tile_y))
            else:
                raise Exception(f"Plugin '{tile.plugin_id}' not found")

        except Exception as e:
            logger.error(f"Error loading plugin '{tile.plugin_id}': {e}")
            # Draw error placeholder
            draw = ImageDraw.Draw(main_img)
            self._draw_error_tile(draw, tile, tile_width, tile_height, str(e))

    def _draw_error_tile(
        self,
        draw: ImageDraw.ImageDraw,
        tile: TileConfig,
        tile_width: int,
        tile_height: int,
        error_msg: str,
    ):
        """Draw an error placeholder for a tile"""
        tile_x = tile.x * tile_width
        tile_y = tile.y * tile_height
        tile_w = tile.width * tile_width
        tile_h = tile.height * tile_height

        # Draw error background
        draw.rectangle(
            [tile_x, tile_y, tile_x + tile_w, tile_y + tile_h],
            fill=(255, 200, 200) if draw.im.mode == "RGB" else 0,
        )

        # Draw error text
        try:
            error_font = get_font("Jost", font_size=12, font_weight="normal")
            if error_font is None:
                error_font = ImageFont.load_default()
        except Exception:
            error_font = ImageFont.load_default()

        error_text = f"Error: {tile.plugin_id}"
        text_bbox = draw.textbbox((0, 0), error_text, font=error_font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        text_x = tile_x + (tile_w - text_w) // 2
        text_y = tile_y + (tile_h - text_h) // 2

        draw.text(
            (text_x, text_y),
            error_text,
            font=error_font,
            fill=(0, 0, 0) if draw.im.mode == "RGB" else 1,
        )

    def _create_tile_device_config(
        self, original_config, tile_dimensions: Tuple[int, int]
    ):
        """Create a device config for a specific tile"""

        class TileDeviceConfig:
            def __init__(self, original, dimensions):
                self.original = original
                self.dimensions = dimensions

            def get_resolution(self):
                return self.dimensions

            def get_config(self, key, default=None):
                return self.original.get_config(key, default)

            def load_env_key(self, key):
                return self.original.load_env_key(key)

        return TileDeviceConfig(original_config, tile_dimensions)

    def _get_plugin_class_name(self, plugin_id: str) -> str:
        """Get the class name for a plugin ID"""
        # This is a simplified mapping - in a real implementation,
        # you'd read this from the plugin-info.json files
        class_mapping = {
            "clock": "Clock",
            "weather": "Weather",
            "calendar": "Calendar",
            "schoolmenu": "SchoolMenu",
            "ai_text": "AiText",
            "ai_image": "AiImage",
            "apod": "Apod",
            "comic": "Comic",
            "image_folder": "ImageFolder",
            "image_upload": "ImageUpload",
            "image_url": "ImageUrl",
            "newspaper": "Newspaper",
            "screenshot": "Screenshot",
            "unsplash": "Unsplash",
            "wpotd": "Wpotd",
        }
        return class_mapping.get(plugin_id, plugin_id.title())

    def get_available_plugins(self, device_config) -> List[Dict[str, str]]:
        """Get list of available plugins for tile configuration"""
        plugins = device_config.get_plugins()
        available_plugins = []

        for plugin in plugins:
            # Skip the tile plugin itself to avoid recursion
            if plugin.get("id") != "tile":
                available_plugins.append(
                    {
                        "id": plugin.get("id"),
                        "display_name": plugin.get(
                            "display_name", plugin.get("id", "Unknown")
                        ),
                    }
                )

        return available_plugins
