import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from typing import List, Dict, Set
from collections import defaultdict
import re
from typing import Dict

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.bubble_base import BubbleBaseModel
from src.logging_config import get_logger
from src.mappings import FIELD_MAPPING
from src.models import FaultDirection

logger = get_logger("utils")

# Load environment variables
load_dotenv()

# Security scheme
security = HTTPBearer()

# Load log directory and level from environment variables


# Create a module-level singleton dependency
get_credentials = Security(security)

def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(get_credentials)):
    """Verify Bearer token in request header."""
    expected_token = os.getenv("BUBBLE_API_KEY")
    if not expected_token or credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")


def map_request_fields(request_data: dict[str, Any]) -> dict[str, Any]:
    """Map incoming fields to the expected fields based on FIELD_MAPPING."""
    mapped_data = {}
    for key, value in request_data.items():
        # Use the mapped field name if it exists, otherwise keep the original key
        mapped_key = FIELD_MAPPING.get(key, key)
        mapped_data[mapped_key] = value
    return mapped_data


# async def upload_to_bubble(file_path: str, api_url: str, project_id: str) -> dict:
#     """Upload the generated file to Bubble API."""
#     try:
#         with open(file_path, "rb") as file:
#             response = await httpx.post(
#                 f"{api_url}/{project_id}",
#                 files={"file": (file_path, file, "application/octet-stream")}
#             )
#             response.raise_for_status()
#             return response.json()
#     except httpx.RequestError as e:
#         raise Exception(f"Error uploading file to Bubble API: {str(e)}")


def log_request(request_data: Any, message_type: str = None):
    """
    Log incoming request data along with an optional message type.

    Args:
        request_data: The data to log
        message_type: Optional category to prefix the message with
    """
    if message_type:
        # Use DEBUG level for request logs to avoid cluttering INFO output
        logger.debug(f"{message_type} | {request_data}")
    else:
        pass
        # logger.info(f"📥 Request | {request_data}")


def log_error(error_message):
    """Log an error message with a standardized format."""
    logger.error(f"❌ Error | {error_message}")


def sanitize_data(data: str):
    """Sanitize project name by removing special characters."""
    return (
        ''.join(e for e in data if e.isalnum() or e in [" ", "-"])
        .replace(' ', '_')
        .replace('-', '_')
    )
    
def make_f3dat_filename(project_id: str, project_name: Optional[str], app_version: str) -> str:
    """
    Generates a safe filename for .f3dat using project_name if available,
    otherwise falls back to project_id.
    """
    base = sanitize_data(project_name) if project_name else sanitize_data(project_id)
    return f"{base}_{app_version}.f3dat"

def extract_project_name_from_f3dat(contents: str) -> Optional[str]:
    """
    Parse .f3dat contents to extract the project name (fish set @Project_Name = '...').
    Returns the extracted name, or None if not found.
    """
    pattern = r"^\s*fish\s+set\s+@project_name\s*=\s*['\"]?(.*?)['\"]?\s*$"
    for line in contents.splitlines():
        match = re.match(pattern, line.strip(), flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def resolve_placeholders(template: str, replacements: Dict[str, str]) -> str:
    """
    Replace all <token> placeholders in `template` using `replacements`.
    Unmatched placeholders remain unchanged.
    """
    def _repl(match: re.Match) -> str:
        key = match.group(1)
        return replacements.get(key, match.group(0))

    return re.sub(r"<([^>]+)>", _repl, template)


def extract_filename_from_url(url: str) -> str:
    """Extract the filename from a URL with proper handling of URL encoding."""
    from urllib.parse import unquote, urlparse

    # Parse the URL
    parsed_url = urlparse(url)

    # Get the path component and extract the last part as the filename
    path = parsed_url.path
    filename = os.path.basename(unquote(path))

    # If filename is empty, generate a unique name
    if not filename:
        import uuid

        filename = f"file_{uuid.uuid4().hex[:8]}.stl"

    # Ensure filename is sanitized
    filename = sanitize_data(filename)

    return filename


async def fetch_data(api_url: str) -> dict:
    """Fetch data from the given API URL."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        raise Exception(f"Error fetching data from API: {str(e)}") from e


async def download_file(file_url: str, save_directory: Path) -> str:
    """Download a file and save it to the given directory."""
    file_name = file_url.split("/")[-1]
    save_path = save_directory / file_name

    async with httpx.AsyncClient() as client:
        response = await client.get(file_url)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)

    return str(save_path)

def strip_outer_quotes(value: Any) -> Any:
    """Remove surrounding single quotes from a string, if present."""
    if isinstance(value, str) and len(value) >= 2 and value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value

def clean_payload(data: Any) -> Any:
    """
    Recursively strip outer single quotes from all string values in a payload.
    """
    if isinstance(data, dict):
        return {k: clean_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [clean_payload(v) for v in data]
    # Strip quotes on primitives (e.g., strings)
    return strip_outer_quotes(data)


# ============================== #
#   Configuration Builder Utilities   #
# ============================== #


class ConfigBuilder:
    """
    Base class for building configuration files with standardized formatting.
    Used by both StopEx and SlopeX generators.
    """

    def __init__(self, prefix: str = ""):
        self.lines = []
        self.prefix = prefix

    def add_line(self, text: str) -> None:
        """Add a raw text line to the configuration."""
        self.lines.append(text)

    def newline(self) -> None:
        """Add an empty line to the configuration."""
        self.lines.append("")

    def add_section_header(self, title: str) -> None:
        """Add a main section header with standardized formatting."""
        self.add_line(";==============================")
        self.add_line(f";==== {title}")
        self.add_line(";==============================")
        self.newline()

    def subheading(self, title: str) -> None:
        """Add a subheading with standardized formatting."""
        self.add_line(";--------------------")
        self.add_line(f";-- {title}")
        self.add_line(";--------------------")

    def config_line(self, key: str, value: Any) -> None:
        """
        Add a configuration line with the specified key and value.

        Parameters:
            key: The configuration key
            value: The value to set (strings will be quoted)
        """
        # Convert IntEnum (e.g., DomainType, DensificationLevel) to numeric value
        try:
            from enum import IntEnum
            if isinstance(value, IntEnum):
                value = value.value
        except ImportError:
            pass
        # Debug logging for densification fields (optional)
        if "densification" in key.lower():
            # print(f"✨ config_line for {key}: value={value} (type: {type(value)})")
            pass

        # Special case for 'notfound' value
        if value == 'notfound':
            self.add_line(f"{self.prefix}set @{key}= ''")
            return

        # Special case for Octree_Mesh to flip yes/no
        if key == "Octree_Mesh" and isinstance(value, str):
            if value.lower() == "true" or value is True:
                value = "no"
            elif value.lower() == "false" or value is False:
                value = "yes"

        # Special case for anisotropy direction - convert to single letter
        if "anisotropy_surface_normal_direction" in key:
            direction_map = {
                "Top": "T",
                "Down": "D",
                "North": "N",
                "South": "S",
                "East": "E",
                "West": "W",
                "top": "T",
                "down": "D",
                "north": "N",
                "south": "S",
                "east": "E",
                "west": "W",
            }

            # If it's a string and matches our map
            if isinstance(value, str) and value in direction_map:
                value = direction_map[value]
                # print(f"Converting direction {key} from full name to letter: {value}")
            # If it has a letter attribute (FaultDirection enum)
            elif hasattr(value, 'letter'):
                value = value.letter
                print(f"Extracting letter from direction enum: {value}")

        # Special case for Fault normal_direction: always map to single-letter code
        if key.lower().endswith("normal_direction"):
            try:
                from src.bubble_base import parse_enum
                from src.enums import FaultDirection
                # Attempt to parse value into enum member
                enum_member = parse_enum(FaultDirection, value, default=None)
                if enum_member:
                    value = enum_member.first_letter()
                else:
                    # Fallback: uppercase first letter of cleaned string
                    s = str(value).strip().strip("'\"")
                    value = s[0].upper() if s else value
            except Exception:
                # Leave original value if mapping fails
                pass
        # Convert booleans to "yes"/"no"
        if isinstance(value, bool):
            value = "yes" if value else "no"

        # Handle None values - convert to empty string
        if value is None:
            value_str = "''"
        # Format floats in scientific notation to decimal format
        elif isinstance(value, float) or (
            isinstance(value, str) and str(value).lower().startswith('1e-')
        ):
            try:
                # If it's already a string in scientific notation (e.g., '1e-05')
                if isinstance(value, str) and ('e' in str(value).lower()):
                    value = float(value)

                # Check if this is a small value in scientific notation
                str_value = str(value)
                if 'e-' in str_value.lower():
                    # Convert to decimal format
                    value_str = f'{float(value):.10f}'.rstrip('0').rstrip('.')
                else:
                    value_str = str(value)
            except (ValueError, TypeError):
                value_str = str(value)
        # Wrap string values in quotes - except for "not found"
        elif isinstance(value, str):
            if value == "not found":
                value_str = "''"  # Convert "not found" to empty string
            else:
                value_str = f"'{value}'"
        else:
            value_str = str(value)

        # Log the final output for debug
        if "densification" in key.lower():
            # print(f"  - Final output: {self.prefix}set @{key}= {value_str}")
            pass

        self.add_line(f"{self.prefix}set @{key}= {value_str}")

    def add_config_line(
        self,
        key: str,
        collection: list,
        identifier: str,
        field: str,
        ref_lib: dict | None = None,
        default: Any = None,
    ) -> None:
        """
        Searches the provided collection for an object whose 'name' (case-insensitive)
        matches the given identifier and outputs a config line for the specified field.
        If a ref_lib is provided, uses mapped_value to fetch the value.
        """
        for item in collection:
            if str(getattr(item, "name", "")).strip().lower() == identifier.lower():
                if ref_lib is not None:
                    val = mapped_value(item, field, ref_lib, default)
                else:
                    val = getattr(item, field, default)
                self.config_line(key, val)
                return
        self.config_line(key, default)

    def add_section_recursive(
        self,
        title: str,
        collection: list[Any],
        field_mappings: list[tuple[str, str, Any]],
        ref_lib: dict | None = None,
        with_heading: bool = True,
        identifier_key: str | None = None,
    ) -> None:
        """
        Adds a recursive section using either numeric index or named identifier.

        Parameters:
            title: Section name
            collection: List of data objects
            field_mappings: List of (key_template, field_name, default)
            ref_lib: Optional reference library
            with_heading: Whether to print subheadings
            identifier_key: Optional attribute name to use instead of index (e.g., 'name')
        """
        try:
            for index, item in enumerate(collection, start=1):
                try:
                    # Determine the identifier to use
                    if identifier_key:
                        identifier = getattr(item, identifier_key, None)
                        if not identifier:
                            print(
                                f"⚠️ Skipping item with missing identifier '{identifier_key}' in {title}"
                            )
                            continue
                        identifier_safe = str(identifier).replace(" ", "_")
                    else:
                        identifier_safe = index

                    if with_heading:
                        heading_label = (
                            f"{title} {identifier_safe}"
                            if identifier_key
                            else f"{title} #{index}"
                        )
                        self.subheading(heading_label)

                    print(f"✨ Processing {title} {identifier_safe}")

                    for key_template, field_name, default in field_mappings:
                        try:
                            # Support key formatting via {index} or {name}
                            output_key = key_template.format(
                                index=index, name=identifier_safe
                            )
                            key_template.replace("{index}", "<index>").replace(
                                "{name}", "<name>"
                            )

                            # Custom handling for Densification enums
                            if field_name == "pit_densification_intensity":
                                dens = getattr(item, field_name, None)
                                if hasattr(dens, "numeric_value"):
                                    val = dens.numeric_value
                                elif hasattr(dens, "value"):
                                    val = dens.value
                                else:
                                    val = default
                            elif field_name in [
                                "pit_upload",
                                "pit_upload_phreatic_surface",
                            ]:
                                val = getattr(item, field_name, default)
                                if val is None:
                                    val = default
                                if not isinstance(val, str):
                                    val = str(val) if val else ""
                            elif ref_lib:
                                val = mapped_value(item, field_name, ref_lib, default)
                            else:
                                # Handle boolean type inference
                                raw_val = getattr(item, field_name, None)
                                if isinstance(default, bool):
                                    if isinstance(raw_val, bool):
                                        val = raw_val
                                    elif isinstance(raw_val, str):
                                        val = raw_val.lower() in ("yes", "true", "1")
                                    elif isinstance(raw_val, int | float):
                                        val = bool(raw_val)
                                    else:
                                        val = default
                                else:
                                    val = raw_val if raw_val is not None else default

                            print(f"  Output key: {output_key} = {val}")
                            self.config_line(output_key, val)

                        except Exception as e:
                            print(f"⚠️ Error in field {field_name}: {e}")
                            self.config_line(output_key, default)

                    self.newline()

                except Exception as e:
                    print(f"⚠️ Error processing item in {title}: {e}")

        except Exception as e:
            print(f"⚠️ Critical error in section {title}: {e}")
            self.add_line(f"; Error in {title}: {e}")

    def add_grouped_section_recursive(
        self,
        title: str,
        collection: list,
        groups: list[tuple[str, list[tuple[str, str, Any]]]],
        ref_lib: dict | None = None,
    ) -> None:
        """
        For each item in the collection, outputs a block of properties grouped by subheadings.

        Parameters:
        - title: Overall title for the recursive block (e.g., "Rockmass Domains").
        - collection: The list of items (e.g., domains).
        - groups: A list of tuples, each of the form:
                    (group_heading, field_mappings)
                    where field_mappings is a list of tuples:
                    (key_template, field_name, default)
        - ref_lib: Optional reference library for mapped values.
        """
        import logging

        logging.getLogger("utils")

        for index, item in enumerate(collection, start=1):
            # Process each group of properties for this item.
            for group_heading, field_mappings in groups:
                # Add a subheading for the property group.
                self.subheading(group_heading)
                for key_template, field_name, default in field_mappings:
                    # Format the output key with the domain index
                    output_key = key_template.format(index=index)
                    # Keep lookup_key as is - it's already correctly formatted
                    lookup_key = field_name

                    # Fetch the value using the reference library if available
                    if ref_lib:
                        # Use lookup_key directly without modification
                        mapping = ref_lib.get(lookup_key)
                        if mapping:
                            internal_name = mapping.get("internal_name")
                            # Get value using internal_name from the reference library
                            val = get_value(item, internal_name, default)
                        else:
                            # Fall back to direct attribute access if not in ref_lib
                            val = getattr(item, field_name, default)
                    else:
                        # Handle the case when there's no ref_lib
                        val = getattr(item, field_name, default)

                    # Handle Rock_or_Soil: always output numeric code (1=Soil, 2=Rock)
                    if field_name == "<domain_name>_Rock_or_Soil":
                        dt = getattr(item, 'domain_type', None)
                        if hasattr(dt, 'numeric_value'):
                            val = dt.numeric_value
                        else:
                            raw = val
                            raw_str = str(raw).lower()
                            val = 2 if 'rock' in raw_str else 1

                    self.config_line(output_key, val)
                self.newline()  # End group
            self.newline()  # End item

    def add_stress_details_section_grouped(
        self,
        stress_detail_names: list[str],
        collection: list[Any],
        field_mappings: list[tuple[str, Any]],
        ref_lib: dict | None = None,
    ) -> None:
        """
        Groups stress detail objects by their 'name' (case-insensitive) and for each stress detail name
        provided (e.g., "maximum", "minimum", "intermediate"), outputs one block of configuration lines.

        The key templates in field_mappings should contain the placeholder "<stress_detail_name>".

        Parameters:
        - stress_detail_names: List of stress detail names to process
        - collection: List of stress detail objects
        - field_mappings: List of tuples with key templates and default values
        - ref_lib: Optional reference library for mapped values
        """

        # Process field mapping function
        def process_field_mapping(
            item: Any,
            index: int,
            key_template: str,
            field_name: str,
            default: Any,
            ref_lib: dict | None = None,
            detail_name: str | None = None,
        ) -> tuple[str, Any]:
            """Process a single field mapping to determine output key and value."""
            # Basic implementation - can be enhanced with key resolution
            output_key = key_template.replace("<stress_detail_name>", detail_name)

            # Determine the value
            if ref_lib:
                mapping = ref_lib.get(key_template)
                if mapping:
                    internal_name = mapping.get("internal_name")
                    val = get_value(item, internal_name, default)
                else:
                    val = getattr(item, field_name, default)
            else:
                val = getattr(item, field_name, default)

            return output_key, val

        # Create a dictionary grouping stress details by lowercased name
        groups = {name.lower(): [] for name in stress_detail_names}
        for item in collection:
            item_name = getattr(item, "name", "").strip().lower()
            if item_name in groups:
                groups[item_name].append(item)

        # Now for each stress detail type, output a block
        for detail in stress_detail_names:
            key = detail.lower()
            if groups.get(key):
                # Use the first matching stress detail
                item = groups[key][0]
                # Use index 1 or adjust as needed
                for key_template, default in field_mappings:
                    output_key, val = process_field_mapping(
                        item, 1, key_template, "", default, ref_lib, detail_name=detail
                    )
                    self.config_line(output_key, val)
                self.newline()

    def add_details_by_name(
        self,
        collection: list[Any],
        mappings_by_name: dict[
            str, list[tuple[str, str, Any] | tuple[str, str, Any, Any]]
        ],
        ref_lib: dict | None = None,
        name_field: str = "name",
        custom_headings: dict[str, str] | None = None,
        add_subheadings: bool = True,
    ) -> None:
        """
        A more generic approach for handling collections like model_construction_details
        or insitu_stress_details where you need to group by name and apply different
        mappings to each named group.

        Parameters:
        - collection: List of objects to process
        - mappings_by_name: Dictionary mapping object names to their field mappings
                          Each name maps to a list of tuples in one of these formats:
                          - (output_key, field_name, default)
                          - (output_key, field_name, default, source_object)
        - ref_lib: Optional reference library for mapped values
        - name_field: The field name used to identify objects (default: "name")
        - custom_headings: Optional dictionary mapping object names to custom heading text
                        For example: {"Stoping": "Stope"}
        - add_subheadings: Whether to add subheadings for each group (default: True)
                        Set to False to skip adding subheadings

        Example:
            mappings = {
                "Stoping": [
                    ("stoping_geometry_filename", "file", ""),
                    ("zone_densification_extent_stoping", "zone_dens_dist", 0)
                ],
                "Topography": [
                    # First tuple uses a separate source object (model_construction)
                    ("_include_topo", "_include_topo", False, model_construction),
                    # Regular mappings from the detail item
                    ("topo_geometry_filename", "file", ""),
                    ("zone_densification_extent_topo", "zone_dens_dist", 0)
                ]
            }

            # With custom heading for Stoping
            custom_headings = {"Stoping": "Stope"}
            builder.add_details_by_name(model_construction_details, mappings, ref_lib,
                                      custom_headings=custom_headings)

            # Skip adding subheadings (for stress details or similar)
            builder.add_details_by_name(stress_details, stress_mappings, ref_lib,
                                      add_subheadings=False)
        """
        # Initialize custom_headings if None
        custom_headings = custom_headings or {}

        # Group objects by name
        grouped_items = {}
        for item in collection:
            raw_value = getattr(item, name_field, "")
            item_name = (
                raw_value.value
                if isinstance(raw_value, Enum)
                else str(raw_value).strip()
            )

            if not item_name:
                continue

            if item_name not in grouped_items:
                grouped_items[item_name] = []
            grouped_items[item_name].append(item)

        # Process each group with its specific mappings
        for name, items in grouped_items.items():
            # Skip if we don't have mappings for this name
            if name not in mappings_by_name:
                logger.debug(f"No mappings defined for {name}, skipping")
                continue

            # Get mapping for this name and process first item
            mappings = mappings_by_name[name]
            if not items:
                continue

            item = items[0]  # Use the first item

            # Add subheading if requested
            if add_subheadings:
                # Use custom heading if specified, otherwise use the object name
                heading = custom_headings.get(name, name)
                self.subheading(heading)

            # Process each mapping
            for mapping in mappings:
                # Handle both 3-tuple and 4-tuple formats
                if len(mapping) == 4:
                    output_key, field_name, default, source_object = mapping
                    # If a source_object is provided in the mapping, use it instead of the item
                    if ref_lib is not None:
                        val = mapped_value(source_object, field_name, ref_lib, default)
                    else:
                        val = getattr(source_object, field_name, default)
                else:
                    output_key, field_name, default = mapping
                    if ref_lib is not None:
                        val = mapped_value(item, field_name, ref_lib, default)
                    else:
                        val = getattr(item, field_name, default)

                self.config_line(output_key, val)

            # Add a newline after each section
            self.newline()

    def build(self) -> str:
        """
        Build and return the complete configuration text.

        Returns:
            String containing the full configuration
        """
        return "\n".join(self.lines)

    # def add_host_domain_section(self, field_groups, domain=None, ref_lib=None):
    #     for group_heading, field_mappings in field_groups:
    #         self.subheading(group_heading)
    #         for key_template, field_name, default in field_mappings:
    #             output_key = key_template.replace("domain{index}", "host")
    #             key_template.replace("domain{index}", "<domain_name>")
    #             val = getattr(domain, field_name, default) if domain else default

    #             if field_name == "<domain_name>_Rock_or_Soil" and hasattr(
    #                 domain, "domain_type"
    #             ):
    #                 val = domain.domain_type.value

    #             self.config_line(output_key, val)
    #         self.newline()


def get_value(obj: Any, key: str, default: Any = "") -> Any:
    """
    Safely get a value from an object or dictionary.

    Parameters:
        obj: Object or dictionary to extract value from
        key: Key or attribute name to look up
        default: Default value if key is not found

    Returns:
        The value if found, otherwise the default
    """
    try:
        return getattr(obj, key, default)
    except Exception:
        if isinstance(obj, dict):
            return obj.get(key, default)
    return default


def sort_by_index(items: list) -> list:
    """
    Sort a list of items by their 'index' attribute.

    Parameters:
        items: List of objects to sort

    Returns:
        Sorted list (or original list if sorting fails)
    """
    try:
        # Assuming each object has an 'index' attribute
        return sorted(items, key=lambda x: int(getattr(x, "index", 0)))
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to sort items by index: {e}")
        return items


def mapped_value(obj: Any, key: str, ref_lib: dict, default: Any = "") -> Any:
    """
    Maps external key to internal field, extracts the value,
    and unwraps Enums for Bubble API compatibility.
    """
    # Special case for anisotropy surface normal direction - always use the letter
    is_anisotropy_direction = "anisotropy_surface_normal_direction" in key
    is_normal_direction = "_normal_direction" in key
    is_rock_or_soil = "_Rock_or_Soil" in key

    mapping = ref_lib.get(key)
    result = (
        get_value(obj, mapping["internal_name"], default)
        if mapping
        else get_value(obj, key, default)
    )

    if result is None and default == 'notfound':
        return 'notfound'

    # Handle empty values for boolean-like fields
    if (result is None or result == "") and any(
        indicator in key.lower()
        for indicator in ["is_", "has_", "include_", "enabled", "custom"]
    ):
        return "no"  # Default empty booleans to 'no'

    # Convert Python booleans to yes/no strings
    if isinstance(result, bool):
        return "yes" if result else "no"

    # Handle Rock_or_Soil fields: faults get numeric codes; domains get string labels
    if is_rock_or_soil:
        # Always emit numeric code for rock_or_soil (1=Soil, 2=Rock)
        try:
            from src.enums import DomainType
            if isinstance(result, DomainType):
                return result.numeric_value
        except ImportError:
            pass
        # Try converting to int
        try:
            iv = int(result)
            if iv in (1, 2):
                return iv
        except Exception:
            pass
        # Fallback string matching
        rs = str(result).strip().lower()
        if "soil" in rs:
            return 1
        if "rock" in rs:
            return 2
        # Default to Rock
        return 2

    # Handle direction fields (anisotropy or normal direction)
    if is_anisotropy_direction or is_normal_direction:
        # If it's an enum with letter property
        if hasattr(result, "letter"):
            return result.letter

        # If it's a string value, map it to the letter
        if isinstance(result, str):
            direction_map = {
                "Top": "T",
                "Down": "D",
                "North": "N",
                "South": "S",
                "East": "E",
                "West": "W",
            }

            # Try case-sensitive first, then try case-insensitive
            if result in direction_map:
                return direction_map[result]

            # Try lowercase match
            for k, v in direction_map.items():
                if result.lower() == k.lower():
                    return v

            # Default to T if no match is found
            return "T"

    # Handle enums
    if isinstance(result, Enum):
        type(result)
        if hasattr(result, "letter"):  # Covers FaultDirection
            return result.letter
        elif hasattr(result, "numeric_value"):  # Covers DensificationLevel
            return result.numeric_value
        else:
            return result.value if hasattr(result, "value") else str(result)

    # Handle sloppy stringified enums
    if isinstance(result, str) and result in FaultDirection.__members__:
        return FaultDirection[result].letter

    return result


# --- Caching Utilities ---


async def cache_composite_model(
    project_id: str,
    app_version: str,
    composite_obj: Any,
    cache_path_template: str = "cache/composite_{project_id}_{app_version}.json",
    use_cache_flag: bool = True,
) -> None:
    """
    Cache a composite model object to disk.

    Parameters:
        project_id: Project identifier
        app_version: Application version identifier
        composite_obj: The object to cache
        cache_path_template: Template for cache file path
        use_cache_flag: Whether to use cache
    """
    if not use_cache_flag or not composite_obj:
        return

    import os
    import pickle

    cache_file = cache_path_template.format(
        project_id=project_id, app_version=app_version
    )
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "wb") as f:
            pickle.dump(composite_obj, f)
        logger.info(f"Cached composite {app_version} object: {cache_file}")
    except Exception as e:
        logger.error(f"Error caching composite {app_version} object: {e}")


async def load_cached_model(
    project_id: str,
    app_version: str,
    cache_path_template: str = "cache/composite_{project_id}_{app_version}.json",
    use_cache_flag: bool = True,
    reload: bool = False,
) -> Any | None:
    """
    Load a cached composite model from disk if available.

    Parameters:
        project_id: Project identifier
        app_version: Application version identifier
        cache_path_template: Template for cache file path
        use_cache_flag: Whether to use cache
        reload: Whether to force reload (ignoring cache)

    Returns:
        Cached model if available, otherwise None
    """
    if not use_cache_flag or reload:
        return None

    import os
    import pickle

    cache_file = cache_path_template.format(
        project_id=project_id, app_version=app_version
    )
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                logger.info(
                    f"Loading composite {app_version} object from cache: {cache_file}"
                )
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading {app_version} from cache: {e}")

    return None


# ============================== #
#      Reference Library Utilities   #
# ============================== #

# class ReferenceLibraryFilter:
#     """A utility class to handle reference library filtering consistently."""

#     @staticmethod
#     def filter_by_parent_object(ref_lib: dict, parent_object: str) -> dict:
#         """
#         Filters the reference library for items with the specified parent_object.

#         Args:
#             ref_lib: The reference library dictionary
#             parent_object: The parent object to filter by

#         Returns:
#             A filtered dictionary containing only items with the matching parent_object
#         """
#         return {k: v for k, v in ref_lib.items() if v.get('parent_object') == parent_object}

#     @staticmethod
#     def filter_with_template(ref_lib: dict, template_pattern: str) -> dict:
#         """
#         Filters the reference library for items containing a specific template pattern.

#         Args:
#             ref_lib: The reference library dictionary
#             template_pattern: The template pattern to filter by (e.g., "<domain_name>")

#         Returns:
#             A filtered dictionary containing only items with the matching template pattern
#         """
#         return {k: v for k, v in ref_lib.items() if template_pattern in k}

#     @staticmethod
#     def get_value_by_outputfile_name(outputfile_name: str,
#                                      settings_ref_lib: dict,
#                                      composite_obj: Any) -> Optional[Any]:
#         """
#         Looks up a value from the composite object using the outputfile_name from settings_ref_library.

#         Args:
#             outputfile_name: The output file name to look up in the reference library
#             settings_ref_lib: The settings reference library dictionary
#             composite_obj: The composite object containing the actual values

#         Returns:
#             The value from the composite object or None if not found
#         """
#         # Find the mapping in the reference library by outputfile_name
#         for key, mapping in settings_ref_lib.items():
#             if mapping.get('outputfile_name') == outputfile_name:
#                 # Get the internal_name to look up in the composite object
#                 internal_name = mapping.get('internal_name', key)

#                 # Check if composite_obj has 'settings' attribute
#                 if hasattr(composite_obj, 'settings'):
#                     # Convert settings object to dictionary
#                     settings_data = composite_obj.settings.model_dump()
#                     # Look for the value using internal_name
#                     return settings_data.get(internal_name)

#                 return None

#         return None

#     @staticmethod
#     def process_templated_field(template_key: str,
#                                entity_name: str,
#                                template_pattern: str,
#                                field_name: str) -> Optional[str]:
#         """
#         Determines if a field matches a template pattern.

#         Args:
#             template_key: The template key from the reference library
#             entity_name: The name of the entity (domain, fault, etc.)
#             template_pattern: The template pattern (e.g., "<domain_name>")
#             field_name: The field name to check

#         Returns:
#             The field part or None if it doesn't match
#         """
#         if template_pattern in template_key:
#             # Extract the field name part after the prefix (e.g., domain_name_field -> field)
#             prefix = template_pattern.strip('<>') + '_'
#             if prefix in template_key:
#                 field_part = template_key.split("_", 1)[1] if "_" in template_key else ""

#                 # Check if field matches either directly or with prefix removed
#                 if (field_name == field_part or
#                     field_name.replace(f"{template_pattern.strip('<>')}_", "") == field_part):
#                     return field_part
#         return None

#     @staticmethod
#     def generate_config_lines_from_model(model_data: dict, ref_lib: dict, parent_object: str) -> List[Any]:
#         """
#         Generate configuration lines from a model using the reference library.
#         Works with both simple and templated object fields.

#         Args:
#             model_data: Dictionary representation of the model data
#             ref_lib: The reference library dictionary
#             parent_object: The parent object type for filtering the reference library

#         Returns:
#             List of ConfigLine objects created from the model data
#         """
#         from src.file_generate_stopex import ConfigLine

#         # Filter ref_lib for items with specified parent_object
#         filtered_ref_lib = ReferenceLibraryFilter.filter_by_parent_object(ref_lib, parent_object)

#         config_lines = []

#         for field, value in model_data.items():
#             # Skip empty values
#             if value is None:
#                 continue

#             # Look for direct match in the filtered reference library
#             mapping = filtered_ref_lib.get(field)

#             # If not found by direct field name, try to find by internal_name
#             if not mapping:
#                 for ref_field, ref_mapping in filtered_ref_lib.items():
#                     if ref_mapping.get('internal_name') == field:
#                         mapping = ref_mapping
#                         break

#             # If mapping found, create ConfigLine
#             if mapping and value is not None:
#                 output_name = mapping['outputfile_name']

#                 # Check if this is a numeric field that shouldn't be quoted
#                 quote_value = not (isinstance(value, (int, float)) or
#                                   (isinstance(value, str) and value.replace('.', '', 1).isdigit()))

#                 config_lines.append(ConfigLine(f"fish set @{output_name} ", value, quote_value=quote_value))

#         return config_lines

#     @staticmethod
#     def generate_templated_config_lines(entity_data: dict, entity_name_field: str,
#                                        ref_lib: dict, parent_object: str,
#                                        template_pattern: str) -> List[Any]:
#         """
#         Generate configuration lines from a templated entity using the reference library.

#         Args:
#             entity_data: Dictionary representation of the entity data
#             entity_name_field: The field name that contains the entity's name
#             ref_lib: The reference library dictionary
#             parent_object: The parent object type for filtering the reference library
#             template_pattern: The template pattern (e.g., "<domain_name>")

#         Returns:
#             List of ConfigLine objects created from the entity data
#         """
#         from src.file_generate_stopex import ConfigLine

#         # Get entity name
#         entity_name = entity_data.get(entity_name_field)
#         if not entity_name:
#             return []

#         # Filter ref_lib for items with specified parent_object
#         filtered_ref_lib = ReferenceLibraryFilter.filter_by_parent_object(ref_lib, parent_object)

#         config_lines = []

#         for field, value in entity_data.items():
#             # Skip the name field itself and empty values
#             if field == entity_name_field or value is None:
#                 continue

#             # Look for template fields in the filtered reference library
#             for template_key, mapping in filtered_ref_lib.items():
#                 if template_pattern in template_key:
#                     field_part = template_key.split("_", 1)[1] if "_" in template_key else ""

#                     # Check direct match or match with prefix removed
#                     field_without_prefix = field.replace(f"{template_pattern.strip('<>')}_", "")
#                     if field == field_part or field_without_prefix == field_part:
#                         output_name = mapping['outputfile_name'].replace(template_pattern, entity_name)

#                         # Check if this is a numeric field that shouldn't be quoted
#                         quote_value = not (isinstance(value, (int, float)) or
#                                           (isinstance(value, str) and value.replace('.', '', 1).isdigit()))

#                         config_lines.append(ConfigLine(f"fish set @{output_name} ", value, quote_value=quote_value))
#                         break

#         return config_lines


# def generate_section_header(title: str, is_subsection: bool = False) -> str:
#     """
#     Generates a formatted section header with comment decorations.

#     Args:
#         title: The title of the section
#         is_subsection: Whether this is a subsection (uses shorter separator)

#     Returns:
#         Formatted section header string
#     """
#     if is_subsection:
#         return f";------------------------------\n;==== {title}\n;------------------------------"
#     else:
#         return f";==============================\n;==== {title}\n;=============================="


# def process_section(data: dict,
#                    ref_lib_filtered: dict,
#                    outputfile_prefix: str = "",
#                    special_handlers: Dict[str, Callable] = None) -> List[str]:
#     """
#     Generic section processor for standard fields using the reference library.

#     Args:
#         data: The data dictionary to process
#         ref_lib_filtered: The filtered reference library
#         outputfile_prefix: Optional prefix for the outputfile_name
#         special_handlers: Optional dictionary of special handlers for specific fields

#     Returns:
#         List of processed lines
#     """
#     lines = []
#     special_handlers = special_handlers or {}

#     for field, value in data.items():
#         # Check if there's a special handler for this field
#         if field in special_handlers:
#             result = special_handlers[field](field, value)
#             if result:
#                 lines.append(result)
#             continue

#         # Standard processing
#         mapping = ref_lib_filtered.get(field)
#         if mapping and value is not None:
#             output_name = mapping['outputfile_name']
#             if outputfile_prefix:
#                 output_name = output_name.replace(outputfile_prefix, outputfile_prefix.strip('<>'))
#             lines.append(f"fish set @{output_name}= '{value}'")

#     return lines


# def process_templated_section(entity_data: dict,
#                              entity_name: str,
#                              ref_lib_filtered: dict,
#                              template_pattern: str) -> List[str]:
#     """
#     Process a section with templated field names.

#     Args:
#         entity_data: The entity data dictionary
#         entity_name: The name of the entity (e.g., domain name, fault name)
#         ref_lib_filtered: The filtered reference library
#         template_pattern: The template pattern (e.g., "<domain_name>")

#     Returns:
#         List of processed lines
#     """
#     lines = []

#     for field, value in entity_data.items():
#         # Skip the name field itself
#         if field == f"{template_pattern.strip('<>')}_name":
#             continue

#         # Look for template fields in the filtered reference library
#         for template_key, mapping in ref_lib_filtered.items():
#             field_part = ReferenceLibraryFilter.process_templated_field(
#                 template_key, entity_name, template_pattern, field)

#             if field_part is not None:
#                 output_name = mapping['outputfile_name'].replace(template_pattern, entity_name)
#                 lines.append(f"fish set @{output_name}= '{value}'")
#                 break

#     return lines


def bubbleify_composite_model(composite_obj: BubbleBaseModel) -> dict[str, Any]:
    """
    🧡 bubbleify_composite_model

    This function takes a large Pydantic composite model (like SlopeXModelConstruction or StopExModelConstruction)
    and transforms it into a Bubble-compatible dictionary that can be PATCHed to the Bubble API.

    Think of it like translating your complex LEGO creation into instructions your friend Bubble can understand.
    Each model piece (enums, file URLs, option sets) gets transformed into Bubble's preferred format.

    It's like sending your LEGO model to customs—you want the right labels, no sharp bits, and everything packed neatly.

    Parameters:
    ----------
    composite_obj : BubbleBaseModel
        The composite Pydantic model that includes fields and submodels already structured with .to_bubble_dict logic.

    Returns:
    -------
    Dict[str, Any]
        A flattened, Bubble API–compatible dictionary ready for PATCH or POST operations.
    """
    if not isinstance(composite_obj, BubbleBaseModel):
        raise TypeError(
            "bubbleify_composite_model expects a BubbleBaseModel-compatible object."
        )

    return composite_obj.to_bubble_dict()


def safe_get(obj: Any, dotted_attr: str, default: Any = None) -> Any:
    """
    Safely get a (potentially dotted) attribute path from an object.
    Example: safe_get(obj, 'project.project_name', 'fallback')
    """
    try:
        for attr in dotted_attr.split("."):
            obj = getattr(obj, attr)
            if obj is None:
                return default
        return obj
    except AttributeError:
        return default


def safe_config_line(
    builder,
    output_key: str,
    value: Any,
    debug: bool = False,
    section: str | None = None,
    missing_fields: list[str] | None = None,
) -> None:
    if value is None:
        msg = f"{output_key} missing or unmapped"
        if section:
            msg = f"[{section}] {msg}"
        if debug:
            builder.add_line(f"; {msg}")
            logger.warning(msg)
        if missing_fields is not None:
            missing_fields.append(msg)
        builder.config_line(output_key, "")
    else:
        builder.config_line(output_key, value)


def get_items_by_type(data: dict, type_key: str) -> list[dict]:
    """
    Utility to extract a list of items from a given key in the full data dictionary.

    Args:
        data: The full project data dictionary.
        type_key: The key corresponding to the item type (e.g., "faults", "rock_mass_domain").

    Returns:
        A list of dictionaries representing the items of that type.
    """
    items = data.get(type_key)
    if items is None:
        return []
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return items
    return []


def find_matching_objects(
    lines: List[str],
    object_prefix: str,
    ref_lib: Dict[str, Dict]
) -> List[Dict]:
    """
    For a given object_prefix (e.g., 'step', 'Domain', 'Backfill'), detect unique object instances
    in the lines, resolve placeholder keys from the ref_lib, and extract matching key-value pairs.

    Returns a list of dicts, one per object, mapping internal names to values.
    """
    objects = defaultdict(dict)
    # Normalize prefix for special-case handling
    lower_prefix = object_prefix.lower()

    # Step 1: Detect unique suffixes or semantic names for this object type
    if lower_prefix == 'step':
        # Numeric steps: only match when 'step' precedes digits (e.g., 'step1', '@step2_')
        # Avoid matching bare numbers elsewhere in the file.
        index_pattern = re.compile(rf"@?{re.escape(object_prefix)}(\d+)\b", re.IGNORECASE)
        # Collect numeric step indices
        index_set = {
            int(m.group(1))
            for line in lines
            for m in index_pattern.finditer(line)
        }
    elif lower_prefix == 'stress_detail_name':
        # Semantic stress-detail names from the InsituStressType enum
        from src.enums import InsituStressType
        names = [e.value for e in InsituStressType]
        # Match any name if it appears in any line (case-insensitive)
        index_set = {
            name for name in names
            if any(name.lower() in line.lower() for line in lines)
        }
    else:
        # Default: numeric suffix after prefix (e.g., Domain1, Fault2)
        # Use case-insensitive matching to capture fish-set keys like 'domain1_*'
        index_pattern = re.compile(rf"{re.escape(object_prefix)}(\d+)", re.IGNORECASE)
        # Collect numeric indices, convert to int for proper ordering
        index_set = {
            int(match.group(1))
            for line in lines
            if (match := index_pattern.search(line))
        }
    logger.info(f"🔬 Found index values for {object_prefix}: {sorted(index_set)}")

    # Step 2: Process each object individually
    for index in sorted(index_set):
        # For stress_detail_name use the enum name directly, else prefix+index
        if lower_prefix == 'stress_detail_name':
            obj_name = index
        else:
            obj_name = f"{object_prefix}{index}"
        # Step 2: Filter lines for this object
        if object_prefix.lower() == 'step':
            # allow explicit 'step1' or bare numeric suffix '1'
            suffix_pattern = re.compile(rf"(?:{re.escape(object_prefix)})?{index}\b", re.IGNORECASE)
            relevant_lines = [line for line in lines if suffix_pattern.search(line)]
            # Fallback: also match patterns like '@step2_' or 'step2=' in variable names
            fallback_patterns = [
                rf"@{re.escape(object_prefix)}{index}[_=]",
                rf"{re.escape(object_prefix)}{index}[_=]"
            ]
            for pat in fallback_patterns:
                relevant_lines += [line for line in lines if re.search(pat, line, re.IGNORECASE)]
            # Deduplicate while preserving order
            seen = set()
            deduped = []
            for l in relevant_lines:
                if l not in seen:
                    seen.add(l)
                    deduped.append(l)
            relevant_lines = deduped
        else:
            # require explicit prefix 'Domain1', 'Fault2', etc.
            relevant_lines = [line for line in lines if obj_name.lower() in line.lower()]


        # Step 3: Build patterns from ref_lib keys with placeholders
        patterns = []
        for key_template, meta in ref_lib.items():
            if "<" not in key_template or ">" not in key_template:
                continue
            internal = meta.get("internal_name")
            if not internal:
                logger.warning(f"⚠️ No internal_name for template '{key_template}', skipping.")
                continue

            # Build replacements: index→numeric index, other tokens→object name
            tokens = re.findall(r"<([^>]+)>", key_template)
            replacements = {}
            for tok in tokens:
                if tok.lower() == "index":
                    # Replace index placeholder with its string representation
                    replacements[tok] = str(index)
                elif tok.lower() in obj_name.lower():
                    replacements[tok] = obj_name
                else:
                    replacements[tok] = obj_name

            resolved_key = resolve_placeholders(key_template, replacements)
            logger.debug(f"🔧 Resolved key: '{resolved_key}' from template '{key_template}' with {replacements}")
            # Allow = or : as delimiter
            pattern = re.compile(rf"{re.escape(resolved_key)}\s*[:=]\s*(.+)", re.IGNORECASE)
            logger.debug(f"🔧 Pattern for '{resolved_key}': {pattern.pattern}")
            patterns.append((resolved_key, internal, pattern))

        # Step 4: Match patterns against the filtered lines
        for line_no, line in enumerate(relevant_lines):
            for resolved_key, internal, pattern in patterns:
                if match := pattern.search(line):
                    # Extract raw value and strip trailing commas/semicolons
                    raw_val = match.group(1).strip()
                    clean_val = re.split(r"[;,]", raw_val, maxsplit=1)[0].strip()
                    # Use internal_name as dictionary key; fallback to resolved_key if missing
                    key = internal or resolved_key
                    objects[obj_name][key] = clean_val
                    # Preserve object identifier
                    objects[obj_name]["name"] = obj_name
                    logger.debug(f"✅ Line {line_no}: Matched {resolved_key} → {key} = {clean_val}")

    logger.info(f"🔍 Built {len(objects)} '{object_prefix}' objects")
    for name, fields in objects.items():
        logger.debug(f"📦 {name}: {fields}")

    return list(objects.values())


def detect_object_keys(lines: list[str], prefix_pattern: str) -> list[str]:
    """
    Detect all object keys matching a prefix pattern followed by digits.
    Example: prefix_pattern='Domain' will detect 'Domain1', 'Domain2', etc.
    """
    import re
    keys = set()
    pattern = re.compile(rf"({prefix_pattern}\d+)")
    for line in lines:
        for m in pattern.finditer(line):
            keys.add(m.group(1))
    return sorted(keys)

def expand_ref_lib_templates(
    ref_section: dict[str, dict],
    object_keys: list[str]
) -> dict[str, dict]:
    """
    Expand templated ref_lib keys by substituting tokens like <index> or <domain_name>
    with actual object_keys. Returns a mapping from resolved F3DAT key to metadata.

    Returns:
        {resolved_key: {
             'internal_name': str,
             'object_key': str,
             'parent_object': str,
             'template_key': str
         }}
    """
    import re
    expanded: dict[str, dict] = {}
    for template_key, info in ref_section.items():
        tpl = info.get("outputfile_name")
        if not tpl or "<" not in tpl:
            continue
        tokens = re.findall(r"<([^>]+)>", tpl)
        for obj_key in object_keys:
            resolved = tpl
            for tok in tokens:
                resolved = resolved.replace(f"<{tok}>", obj_key)
            expanded[resolved] = {
                "internal_name": info.get("internal_name"),
                "object_key": obj_key,
                "parent_object": info.get("parent_object"),
                "template_key": template_key,
            }
    return expanded

def find_matching_objects_general(
    lines: list[str],
    ref_section: dict[str, dict],
    object_keys: list[str]
) -> list[dict]:
    """
    Generalized matching: expand ref_section templates and scan lines for each resolved key.
    Returns a list of dicts having 'name': object_key and mapped internal fields.
    """
    import re
    from collections import defaultdict

    # Expand templates
    expanded = expand_ref_lib_templates(ref_section, object_keys)
    objects: dict[str, dict] = defaultdict(dict)

    # Pattern to extract value after '='
    pattern = re.compile(r"fish set @([\w\d_]+)\s*=\s*['\"]?(.+?)['\"]?$")
    for line in lines:
        m = pattern.search(line.strip())
        if not m:
            continue
        key, raw = m.groups()
        mapping = expanded.get(key)
        if mapping:
            obj = mapping["object_key"]
            internal = mapping["internal_name"]
            # strip quotes
            val = raw.strip()
            objects[obj][internal] = val
            objects[obj]["name"] = obj

    return list(objects.values())
  
def find_matching_objects_from_templates(
    lines: list[str],
    ref_section: dict[str, dict],
    prefix_pattern: str = "step"
) -> list[dict]:
    """
    Shortcut: detect all object keys matching prefix_pattern (e.g., 'step'),
    then expand templated ref_section keys (<index>, <domain_name>, etc.)
    and extract their values from lines.
    Returns list of dicts with 'name': object_key and internal fields.
    """
    # Auto-detect object keys like 'step1', 'step2', etc.
    object_keys = detect_object_keys(lines, prefix_pattern)
    # Delegate to general matcher
    return find_matching_objects_general(lines, ref_section, object_keys)
 
def find_matching_objects_from_dict(
    lines: List[str],
    object_prefix: str,
    ref_section: Dict[str, Dict]
) -> List[Dict[str, Any]]:
    """
    Parse fish-set lines once into a dict, then build per-object mappings using ref_section templates.

    Args:
        lines: List of lines from an F3DAT file.
        object_prefix: Prefix for objects (e.g., 'Domain', 'Fault', 'step', etc.).
        ref_section: Reference-library section mapping template keys to metadata
                     (including 'outputfile_name' and 'internal_name').

    Returns:
        A list of dicts, one per object instance, mapping internal field names to extracted values.
    """
    # Build fish_dict: var_name.lower() -> raw string value
    fish_pattern = re.compile(
        r"fish\s+set\s+@([\w\d_]+)\s*=\s*['\"]?(.*?)['\"]?\s*$",
        re.IGNORECASE
    )
    fish_dict: Dict[str, str] = {}
    for line in lines:
        m = fish_pattern.search(line.strip())
        if not m:
            continue
        var, raw = m.groups()
        fish_dict[var.lower()] = raw.strip()

    # Detect object indices from fish_dict keys: e.g., domain3_*
    pref = object_prefix.lower()
    idx_re = re.compile(rf"^{re.escape(pref)}(\d+)_")
    index_set: Set[int] = {
        int(m.group(1))
        for key in fish_dict
        if (m := idx_re.match(key))
    }
    objects: List[Dict[str, Any]] = []
    # For each detected object index
    for idx in sorted(index_set):
        obj_key = f"{pref}{idx}"
        data: Dict[str, Any] = {}
        # For each ref-lib template entry
        for meta in ref_section.values():
            tpl = meta.get("outputfile_name") or ""
            internal = meta.get("internal_name")
            if not tpl or not internal:
                continue
            # Only process templates with placeholders
            if "<" not in tpl:
                continue
            # Resolve placeholder(s)
            resolved = tpl
            for token in re.findall(r"<([^>]+)>", tpl):
                resolved = resolved.replace(f"<{token}>", obj_key)
            # Lookup case-insensitive
            val = fish_dict.get(resolved.lower())
            if val is not None:
                data[internal] = val
        if data:
            data["name"] = obj_key
            objects.append(data)
    return objects
