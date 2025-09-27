"""
School Menu Plugin for InkyPi
Displays school lunch menu information on e-ink display
"""

import logging
from datetime import date, datetime

import pytz
from PIL import Image, ImageDraw, ImageFont

from plugins.base_plugin.base_plugin import BasePlugin
from plugins.schoolmenu.lunch_menu_service import LunchMenuService
from utils.app_utils import get_font

logger = logging.getLogger(__name__)


class SchoolMenu(BasePlugin):
    """Plugin to display school lunch menu"""

    def __init__(self, config, **dependencies):
        super().__init__(config, **dependencies)
        # Will be initialized in generate_image with settings
        self.menu_service = None

    def generate_settings_template(self):
        """Generate settings template parameters"""
        template_params = super().generate_settings_template()
        template_params["style_settings"] = "True"
        return template_params

    def generate_image(self, settings, device_config):
        """Generate the school menu image"""
        try:
            # Get settings
            menu_url = settings.get("menuUrl", "").strip()
            num_days = int(settings.get("numDays", 1))
            show_date = settings.get("showDate", True)
            custom_title = settings.get("customTitle", "School Lunch Menu")

            # Validate num_days
            if num_days < 1 or num_days > 7:
                num_days = 1

            # Initialize service with URL if provided
            if menu_url:
                self.menu_service = LunchMenuService(menu_url=menu_url)
            else:
                self.menu_service = LunchMenuService()

            # Get menu data for specified days
            menu_data = self.menu_service.get_menu_for_days(num_days)

            # Get device configuration
            dimensions = device_config.get_resolution()
            if device_config.get_config("orientation") == "vertical":
                dimensions = dimensions[::-1]

            width, height = dimensions

            # Create image
            if device_config.get_config("color") == "bw":
                img = Image.new("1", (width, height), 1)  # White background
            else:
                img = Image.new(
                    "RGB", (width, height), (255, 255, 255)
                )  # White background

            draw = ImageDraw.Draw(img)

            # Colors based on device type
            if device_config.get_config("color") == "bw":
                text_color = 0  # Black
                accent_color = 0  # Black
            else:
                text_color = (0, 0, 0)  # Black
                accent_color = (50, 50, 150)  # Dark blue

            # Fonts
            try:
                title_font = get_font("Jost", font_size=24, font_weight="bold")
                if title_font is None:
                    title_font = get_font("Jost", font_size=24, font_weight="normal")

                date_font = get_font("Jost", font_size=16, font_weight="normal")
                item_font = get_font("Jost", font_size=14, font_weight="normal")
                small_font = get_font("Jost", font_size=12, font_weight="normal")

                # Fallback to default if any font loading fails
                if any(
                    font is None
                    for font in [title_font, date_font, item_font, small_font]
                ):
                    raise Exception("Font loading failed")

            except Exception as e:
                logger.warning(f"Font loading failed: {e}, using default font")
                title_font = ImageFont.load_default()
                date_font = ImageFont.load_default()
                item_font = ImageFont.load_default()
                small_font = ImageFont.load_default()

            # Layout
            margin = 10
            y_pos = margin

            # Draw title
            title_text = custom_title
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2

            draw.text((title_x, y_pos), title_text, font=title_font, fill=accent_color)
            y_pos += title_bbox[3] - title_bbox[1] + 10

            # Draw date if enabled and single day
            if show_date and num_days == 1:
                # For single day, show the full date
                single_date = date.today()
                date_text = single_date.strftime("%A, %B %d, %Y")
                date_bbox = draw.textbbox((0, 0), date_text, font=date_font)
                date_width = date_bbox[2] - date_bbox[0]
                date_x = (width - date_width) // 2

                draw.text((date_x, y_pos), date_text, font=date_font, fill=text_color)
                y_pos += date_bbox[3] - date_bbox[1] + 15

            # Draw separator line
            line_y = y_pos
            draw.line(
                [(margin, line_y), (width - margin, line_y)], fill=accent_color, width=2
            )
            y_pos += 10

            # Draw menu items for each day
            from datetime import timedelta

            base_date = date.today()

            for day_index, (date_str, menu_items) in enumerate(menu_data.items()):
                # Parse the date from string
                menu_date = date.fromisoformat(date_str)

                # Add day header if multiple days
                if num_days > 1:
                    if day_index > 0:
                        y_pos += 10  # Extra space between days

                    # Day header
                    if menu_date == base_date:
                        day_header = "Today"
                    elif menu_date == base_date + timedelta(days=1):
                        day_header = "Tomorrow"
                    else:
                        day_header = menu_date.strftime("%A")

                    if show_date:
                        day_header += f" ({menu_date.strftime('%m/%d')})"

                    day_bbox = draw.textbbox((0, 0), day_header, font=date_font)
                    day_height = day_bbox[3] - day_bbox[1]

                    # Check if we have space
                    if y_pos + day_height + 20 > height - margin:
                        more_days = len(menu_data) - day_index
                        more_text = f"... and {more_days} more day{'s' if more_days > 1 else ''}"
                        draw.text(
                            (margin, y_pos), more_text, font=small_font, fill=text_color
                        )
                        break

                    draw.text(
                        (margin, y_pos), day_header, font=date_font, fill=accent_color
                    )
                    y_pos += day_height + 5

                # Draw menu items for this day
                if not menu_items:
                    no_menu_text = "No menu available"
                    draw.text(
                        (margin + 15, y_pos),
                        no_menu_text,
                        font=item_font,
                        fill=text_color,
                    )
                    y_pos += draw.textbbox((0, 0), no_menu_text, font=item_font)[3] + 5
                else:
                    items_displayed = 0
                    for item in menu_items:
                        # Check if we have space for more items
                        item_bbox = draw.textbbox((0, 0), item, font=item_font)
                        item_height = item_bbox[3] - item_bbox[1]

                        if (
                            y_pos + item_height + 5 > height - margin - 30
                        ):  # Reserve space for timestamp
                            remaining = len(menu_items) - items_displayed
                            if remaining > 0:
                                more_text = f"... and {remaining} more items"
                                draw.text(
                                    (margin + 20, y_pos),
                                    more_text,
                                    font=small_font,
                                    fill=text_color,
                                )
                            return img  # Exit early if no more space

                        # Draw bullet point
                        bullet_x = margin + (15 if num_days > 1 else 0)
                        bullet_y = y_pos + (item_height // 2)
                        draw.ellipse(
                            [bullet_x, bullet_y - 2, bullet_x + 4, bullet_y + 2],
                            fill=accent_color,
                        )

                        # Draw menu item
                        text_x = bullet_x + 15
                        draw.text(
                            (text_x, y_pos), item, font=item_font, fill=text_color
                        )
                        y_pos += item_height + 3
                        items_displayed += 1

            # Add refresh time at bottom if there's space
            if y_pos < height - 30:
                timezone = device_config.get_config(
                    "timezone", default="America/New_York"
                )
                time_format = device_config.get_config("time_format", default="12h")
                tz = pytz.timezone(timezone)
                now = datetime.now(tz)

                if time_format == "12h":
                    time_str = now.strftime("Updated: %I:%M %p")
                else:
                    time_str = now.strftime("Updated: %H:%M")

                time_bbox = draw.textbbox((0, 0), time_str, font=small_font)
                time_width = time_bbox[2] - time_bbox[0]
                time_x = (width - time_width) // 2
                time_y = height - margin - (time_bbox[3] - time_bbox[1])

                draw.text((time_x, time_y), time_str, font=small_font, fill=text_color)

            logger.info("School menu image generated successfully")
            return img

        except Exception as e:
            logger.error(f"Error generating school menu image: {str(e)}")
            raise RuntimeError(f"Failed to generate school menu image: {str(e)}")
