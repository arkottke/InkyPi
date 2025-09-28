"""
School Menu Plugin for InkyPi
Displays school lunch menu information on e-ink display

This plugin fetches real menu data from School Nutrition and Fitness websites using GraphQL API.

Settings:
- menuId: Menu ID from the School Nutrition website URL (e.g., 68750f9b40a2c835145a7cc2)
- siteCode: Optional site code if present in URL (e.g., 894)
- numDays: Number of days to display (1-5)
- customTitle: Custom title for the menu display
- fontSize: Font size for menu items
- showDate: Whether to show dates
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import requests

from plugins.base_plugin.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

# Font scaling options
FONT_SIZES = {
    "small": 0.8,
    "normal": 1.0,
    "large": 1.2,
    "extra_large": 1.4,
}

# Standard lunch items to filter out
STANDARD_ITEMS = [
    "Garden Bar:",
    "Organic Fresh Fruits and Veggies",
    "Straus Organic 1% Milk",
    "Non-fat milk",
    "Low-fat Milk",
    "Milk",
    "Garden Bar: Fresh Fruits and Veggies",
]

# API Configuration
GRAPHQL_API_URL = "https://api.isitesoftware.com/graphql"
API_TIMEOUT = 15
MAX_DAYS = 5
MIN_DAYS = 1


class SchoolMenu(BasePlugin):
    """Plugin to display school lunch menu"""

    def __init__(self, config, **dependencies):
        super().__init__(config, **dependencies)
        # Initialize menu parser - no more mock data

    def generate_settings_template(self):
        """Generate settings template parameters"""
        template_params = super().generate_settings_template()
        template_params["style_settings"] = "True"
        return template_params

    def get_menu_for_days(
        self,
        num_days: int = 1,
        menu_id: Optional[str] = None,
        site_code: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """Get menu items for the specified number of days starting from today"""
        if not self._is_valid_day_count(num_days):
            raise ValueError(
                f"Number of days must be between {MIN_DAYS} and {MAX_DAYS}"
            )

        if menu_id:
            return self._fetch_menu_from_api(num_days, menu_id, site_code)
        else:
            return self._get_empty_menu_for_days(num_days)

    def _is_valid_day_count(self, num_days: int) -> bool:
        """Validate the number of days parameter"""
        return MIN_DAYS <= num_days <= MAX_DAYS

    def _fetch_menu_from_api(
        self, num_days: int, menu_id: str, site_code: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Fetch menu from the GraphQL API using menu ID"""
        try:
            if not menu_id:
                raise ValueError("Menu ID is not provided")

            logger.info(f"Fetching menu data for ID: {menu_id}")
            if site_code:
                logger.info(f"Using site code: {site_code}")

            # Build GraphQL query
            graphql_query = self._build_menu_query(menu_id)

            # Make the GraphQL request
            response = requests.post(
                GRAPHQL_API_URL,
                json=graphql_query,
                headers=self._get_api_headers(),
                timeout=API_TIMEOUT,
            )

            if response.status_code != 200:
                logger.error(f"GraphQL API returned status {response.status_code}")
                return self._get_empty_menu_for_days(num_days)

            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return self._get_empty_menu_for_days(num_days)

            if not data.get("data", {}).get("menu"):
                logger.error("No menu data returned from API")
                return self._get_empty_menu_for_days(num_days)

            menu = data["data"]["menu"]
            return self._parse_graphql_menu_data(menu, num_days)

        except Exception as e:
            logger.error(f"Error fetching menu from API: {e}")
            return self._get_empty_menu_for_days(num_days)

    def _build_menu_query(self, menu_id: str) -> dict:
        """Build GraphQL query for menu data"""
        return {
            "query": """query {
                menu(id: \"%s\") {
                    name
                    month
                    year
                    items {
                        day
                        month
                        year
                        date
                        product {
                            name
                        }
                    }
                }
            }"""
            % menu_id
        }

    def _get_api_headers(self) -> dict:
        """Get headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }

    def _parse_graphql_menu_data(
        self, menu: dict, num_days: int
    ) -> Dict[str, List[str]]:
        """Parse menu data from GraphQL response"""
        try:
            # Validate menu structure
            menu_month, menu_year = self._extract_menu_dates(menu)
            if not menu_month or not menu_year:
                return self._get_empty_menu_for_days(num_days)

            # Group items by day
            daily_items = self._group_items_by_day(menu.get("items", []))

            # Convert to date-based format
            menu_data = self._convert_to_date_format(
                daily_items, menu_month, menu_year, num_days
            )

            logger.info(f"Successfully parsed menu data for {len(menu_data)} days")
            return menu_data

        except Exception as e:
            logger.error(f"Error parsing GraphQL menu data: {e}")
            return self._get_empty_menu_for_days(num_days)

    def _extract_menu_dates(self, menu: dict) -> tuple[Optional[int], Optional[int]]:
        """Extract month and year from menu data"""
        menu_month = menu.get("month")
        menu_year = menu.get("year")

        if not menu_month or not menu_year:
            logger.error("Menu missing month or year information")
            return None, None

        return menu_month, menu_year

    def _group_items_by_day(self, items: List[dict]) -> Dict[int, List[str]]:
        """Group menu items by day of month"""
        daily_items = {}

        for item in items:
            day = item.get("day")
            product = item.get("product", {})
            product_name = product.get("name")

            if day and product_name and str(product_name).strip():
                if day not in daily_items:
                    daily_items[day] = []

                # Clean the product name - remove colons and extra whitespace
                cleaned_name = str(product_name).strip().rstrip(":")
                if cleaned_name and cleaned_name not in daily_items[day]:
                    daily_items[day].append(cleaned_name)

        return daily_items

    def _convert_to_date_format(
        self,
        daily_items: Dict[int, List[str]],
        menu_month: int,
        menu_year: int,
        num_days: int,
    ) -> Dict[str, List[str]]:
        """Convert daily items to date-based format"""
        menu_data = {}
        search_date = date.today()
        days_added = 0

        while days_added < num_days:
            # Skip weekends
            if self._is_school_day(search_date):
                date_str = search_date.strftime("%Y-%m-%d")

                if self._is_date_in_menu_range(search_date, menu_month, menu_year):
                    day_of_month = search_date.day

                    if day_of_month in daily_items:
                        # Filter out standard items
                        items = daily_items[day_of_month]
                        filtered_items = self._filter_standard_items(items)

                        # Only add if we have items after filtering
                        if filtered_items:
                            menu_data[date_str] = filtered_items
                        else:
                            menu_data[date_str] = ["No menu available"]
                    else:
                        menu_data[date_str] = ["No menu available"]
                else:
                    menu_data[date_str] = ["No menu available"]

                days_added += 1

            search_date += timedelta(days=1)

        return menu_data

    def _is_school_day(self, check_date: date) -> bool:
        """Check if the given date is a school day (Monday-Friday)"""
        return check_date.weekday() < 5  # Monday=0, Friday=4

    def _is_date_in_menu_range(
        self, check_date: date, menu_month: int, menu_year: int
    ) -> bool:
        """Check if the given date is within the menu's month/year range"""
        return check_date.month == menu_month and check_date.year == menu_year

    def _get_empty_menu_for_days(self, num_days: int) -> Dict[str, List[str]]:
        """Get empty menu structure for specified number of days, skipping weekends"""
        menu_data = {}
        current_date = date.today()
        days_added = 0

        while days_added < num_days:
            # Skip weekends (Saturday = 5, Sunday = 6)
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                date_str = current_date.strftime("%Y-%m-%d")
                # Return empty list to indicate no menu data available
                menu_data[date_str] = ["Menu not available"]
                days_added += 1

            current_date += timedelta(days=1)

        return menu_data

    def _filter_standard_items(self, menu_items: List[str]) -> List[str]:
        """Filter out standard lunch items like garden bar and milk"""
        filtered_items = []
        for item in menu_items:
            # Check if this item should be filtered out
            should_filter = False
            for standard_item in STANDARD_ITEMS:
                if standard_item.lower() in item.lower():
                    should_filter = True
                    break

            if not should_filter:
                filtered_items.append(item)

        return filtered_items

    def generate_image(self, settings, device_config):
        """Generate the school menu image using HTML/CSS rendering"""
        try:
            # Parse and validate settings
            config = self._parse_settings(settings)

            # Get menu data for specified days
            menu_data = self.get_menu_for_days(
                config["num_days"], config["menu_id"], config["site_code"]
            )

            # Get dimensions
            dimensions = device_config.get_resolution()
            if device_config.get_config("orientation") == "vertical":
                dimensions = dimensions[::-1]

            # Prepare template parameters
            template_params = self._prepare_template_params(
                menu_data, config, settings, device_config
            )

            # Render the image using HTML/CSS
            image = self.render_image(
                dimensions, "menu.html", "menu.css", template_params
            )

            if not image:
                raise RuntimeError("Failed to render menu image, please check logs.")

            logger.info("School menu image rendered successfully using HTML/CSS")
            return image

        except Exception as e:
            logger.error(f"Error generating school menu image: {str(e)}")
            raise RuntimeError(f"Failed to generate school menu image: {str(e)}")

    def _prepare_template_params(
        self,
        menu_data: Dict[str, List[str]],
        config: dict,
        settings: dict,
        device_config,
    ) -> dict:
        """Prepare template parameters for HTML/CSS rendering"""
        from datetime import date, timedelta

        # Get current date info
        today = date.today()
        tomorrow = today + timedelta(days=1)
        today_str = today.strftime("%Y-%m-%d")
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")

        # Prepare formatted dates and day names
        formatted_dates = {}
        day_names = {}

        for date_str in menu_data.keys():
            menu_date = date.fromisoformat(date_str)
            formatted_dates[date_str] = menu_date.strftime("%m/%d")
            day_names[date_str] = menu_date.strftime("%A")

        # Single day date text
        single_date_text = ""
        if len(menu_data) == 1:
            single_date = today
            single_date_text = single_date.strftime("%A, %B %d, %Y")

        # Get timezone and time format for timestamp
        timezone = device_config.get_config("timezone", default="America/New_York")
        time_format = device_config.get_config("time_format", default="12h")

        timestamp = ""
        show_timestamp = True
        try:
            import pytz

            tz = pytz.timezone(timezone)
            now = datetime.now(tz)

            if time_format == "12h":
                timestamp = now.strftime("%I:%M %p")
            else:
                timestamp = now.strftime("%H:%M")
        except Exception as e:
            logger.warning(f"Error generating timestamp: {e}")
            show_timestamp = False

        return {
            "menu_data": menu_data,
            "plugin_settings": settings,
            "font_scale": config["font_scale"],
            "today_str": today_str,
            "tomorrow_str": tomorrow_str,
            "formatted_dates": formatted_dates,
            "day_names": day_names,
            "single_date_text": single_date_text,
            "timestamp": timestamp,
            "show_timestamp": show_timestamp,
        }

    def _parse_settings(self, settings: dict) -> dict:
        """Parse and validate plugin settings"""
        menu_id = settings.get("menuId", "").strip()
        site_code = settings.get("siteCode", "").strip() or None
        num_days = int(settings.get("numDays", 1))
        show_date = settings.get("showDate", True)
        custom_title = settings.get("customTitle", "School Lunch Menu")
        font_size = settings.get("fontSize", "normal")

        # Validate num_days
        if not self._is_valid_day_count(num_days):
            num_days = 1

        return {
            "menu_id": menu_id,
            "site_code": site_code,
            "num_days": num_days,
            "show_date": show_date,
            "custom_title": custom_title,
            "font_size": font_size,
            "font_scale": FONT_SIZES.get(font_size, 1.0),
        }
