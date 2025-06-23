# utils/bubble_base.py

from pydantic import BaseModel, Field, ConfigDict, model_validator
from enum import Enum
from urllib.parse import urlparse, unquote
from typing import Any, Dict, Optional, List
from datetime import datetime

BUBBLE_METADATA_FIELDS = {"_id", "Created Date", "Modified Date", "Created By"}
def strip_empty_fields(d: dict) -> dict:
    """Remove keys with empty values (None, empty string, empty list, empty dict)."""
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def extract_filename_from_url(url: Optional[str]) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    return unquote(parsed.path.split("/")[-1]) or ""
def parse_enum(enum_class, value, default=None):
    if value is None or value == "":
        return default
    try:
        if isinstance(value, enum_class):
            return value
        if isinstance(enum_class, type) and issubclass(enum_class, Enum):
            # Try to match by internal value, name, or human-readable label
            for member in enum_class:
                # Match raw stored value (db key)
                if value == member.value:
                    return member
                # Match Python enum name
                if value == member.name:
                    return member
                # Match human-readable label if present
                label = getattr(member, 'label', None)
                if label is not None and value == label:
                    return member
            # Fallback for numeric option sets: if value is int, map by member order
            if isinstance(value, int):
                members = list(enum_class)
                idx = value - 1
                if 0 <= idx < len(members):
                    return members[idx]
    except Exception:
        pass
    return default

def enum_to_bubble_value(value: Enum, field_name: str) -> Any:
    """
    Convert an Enum to its Bubble-API representation. By default, return the
    enum's internal value (db key). Special-case directions to use their letter code.
    """
    # If it's not an Enum, return unchanged
    if not isinstance(value, Enum):
        return value
    # Special-case: direction fields should use single-letter codes
    if field_name.endswith("_direction") and isinstance(value, Enum):
        # Use the first character of the enum's db_value or label, uppercase
        db_val = getattr(value, 'value', None)
        if isinstance(db_val, str) and db_val:
            return db_val[0].upper()
        lbl = getattr(value, 'label', None)
        if isinstance(lbl, str) and lbl:
            return lbl[0].upper()
    # Special-case: densification_level should use numeric index (1-based)
    if field_name == "densification_level" and hasattr(value, 'numeric_value'):
        return value.numeric_value
    # For densification_intensity fields, return numeric index
    if field_name == "densification_intensity" and hasattr(value, 'numeric_value'):
        return value.numeric_value
    # Generic fallback: use human-readable label if available
    lbl = getattr(value, 'label', None)
    if isinstance(lbl, str):
        return lbl

    # Default: return the raw enum value (db key) or numeric index
    return value.value
   
# Extend Python enums with a numeric_value property for Bubble option-sets
class BubbleEnum(Enum):
    """
    Base class for any Option-Set enums needing a numeric index (1-based) via .numeric_value
    """
    @property
    def numeric_value(self) -> int:
        members = list(self.__class__)
        # 1-based index, so first member is 1
        return members.index(self) + 1

    def first_letter(self) -> str:
        """Return the first letter of the enum's value, uppercase."""
        try:
            return str(self.value)[0].upper()
        except Exception:
            return str(self.value)[0]

    @classmethod
    def get_by_value(cls, val: str):
        """Lookup enum member by its .value; returns None if not found."""
        for member in cls:
            if member.value == val:
                return member
        return None

def model_to_bubble(
    model: BaseModel,
    upload_file_url: Optional[str] = None,
    file_fields: Optional[List[str]] = None,
    enum_overrides: Optional[Dict[str, str]] = None
) -> dict:
    file_fields = file_fields or []
    enum_overrides = enum_overrides or {}

    # ✅ USE by_alias=True
    # Build both filtered and unfiltered dumps so we can re-insert any non-None fields
    full_data = model.model_dump(by_alias=True, exclude_none=False)
    raw_data = model.model_dump(by_alias=True, exclude_none=True)
    # Debug: log keys in full vs filtered dumps
    try:
        from logging_config import logger as _logger
        _logger.debug(f"🗃️ full_data keys in model_to_bubble: {list(full_data.keys())}")
        _logger.debug(f"🗃️ raw_data keys in model_to_bubble: {list(raw_data.keys())}")
    except ImportError:
        pass
    # Re-insert any populated fields that were dropped by exclude_none
    for k, v in full_data.items():
        if k not in raw_data and v is not None:
            raw_data[k] = v

    cleaned = {k: v for k, v in raw_data.items() if k not in BUBBLE_METADATA_FIELDS}

    for k, v in list(cleaned.items()):
        if isinstance(v, Enum):
            override = enum_overrides.get(k)
            if override == "numeric":
                # Use numeric_value property or raw value as fallback
                cleaned[k] = getattr(v, "numeric_value", v.value)
            elif override == "str":
                # Use enum's __str__ (human-readable) instead of raw value
                cleaned[k] = str(v)
            elif override == "value":
                # Use the raw enum value (e.g. 'simple', 'minimum')
                cleaned[k] = v.value
            elif override == "name":
                # Use the enum member name (e.g. 'Simple', 'Minimum')
                cleaned[k] = v.name
            elif override == "key":
                # Convert the display label into a Bubble option-set key
                # lower-case, replace spaces with underscores
                cleaned[k] = str(v).lower().replace(" ", "_")
            else:
                cleaned[k] = enum_to_bubble_value(v, k)

    # ✅ Convert booleans to "yes"/"no"
    for k, v in list(cleaned.items()):
        if isinstance(v, bool):
            cleaned[k] = "yes" if v else "no"

    for field in file_fields:
        if cleaned.get(field) is not None:
            cleaned[field] = extract_filename_from_url(cleaned[field])

    if upload_file_url and "upload_file" in cleaned:
        cleaned["upload_file"] = extract_filename_from_url(upload_file_url)

    # 🔧 Ensure all keys use alias names in case anything was added in snake_case
    alias_map = {}
    for key, field in model.model_fields.items():
        if hasattr(field, 'alias') and field.alias:
            alias_map[field.alias] = key

    cleaned = {alias_map.get(k, k): v for k, v in cleaned.items()}

    return cleaned



class BubbleBaseModel(BaseModel):
    created_date: Optional[datetime] = Field(default=None, alias="Created Date", exclude=True)
    modified_date: Optional[datetime] = Field(default=None, alias="Modified Date", exclude=True)
    created_by: Optional[str] = Field(default=None, alias="Created By", exclude=True)
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @model_validator(mode="before")
    def _strip_file_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically strip URL components from any file_fields defined in Meta.
        """
        file_fields = getattr(getattr(cls, 'Meta', None), 'file_fields', [])
        for field in file_fields:
            if field in values:
                values[field] = extract_filename_from_url(values[field])
        return values

    def strip_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in data.items() if k not in BUBBLE_METADATA_FIELDS}

    def convert_enums(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in list(data.items()):
            if isinstance(v, Enum):
                data[k] = enum_to_bubble_value(v, k)
        return data

    def to_bubble_dict(self, upload_file_url: Optional[str] = None) -> dict:
        file_fields = getattr(self.__class__, 'Meta', None)
        file_fields = getattr(file_fields, 'file_fields', [])
        enum_overrides = getattr(self.__class__, 'Meta', None)
        enum_overrides = getattr(enum_overrides, 'enum_overrides', {})

        data = model_to_bubble(
            self,
            upload_file_url=upload_file_url,
            file_fields=file_fields,
            enum_overrides=enum_overrides,
        )
        # Remove any empty values so we don't send blanks that overwrite existing data
        return strip_empty_fields(data)
    
    def to_patch_dict(self, upload_file_url: Optional[str] = None) -> dict:
        """
        Convert only explicitly set or changed fields to a Bubble-friendly dict,
        omitting defaults, unset, and None values (for PATCH operations).
        """
        # Dump model excluding unset, defaults, and None
        data = self.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_defaults=True,
            exclude_unset=True,
        )
        # Convert any Enum instances
        data = self.convert_enums(data)
        # Normalize numeric enum inputs into correct db_value strings
        from enum import Enum as _Enum
        for key, value in list(data.items()):
            # If an enum field came through as an int, map it to the db_value
            if isinstance(value, int) and key in self.model_fields:
                enum_cls = getattr(self.model_fields[key], 'annotation', None)
                if isinstance(enum_cls, type) and issubclass(enum_cls, _Enum):
                    member = parse_enum(enum_cls, value)
                    if member is not None:
                        data[key] = enum_to_bubble_value(member, key)
        # Convert booleans to "yes"/"no"
        for k, v in list(data.items()):
            if isinstance(v, bool):
                data[k] = "yes" if v else "no"
        # Handle file fields
        file_fields = getattr(self.__class__.Meta, "file_fields", [])
        for field in file_fields:
            if data.get(field) is not None:
                data[field] = extract_filename_from_url(data[field])
        # Optional override for single upload_file URL
        if upload_file_url and "upload_file" in data:
            data["upload_file"] = extract_filename_from_url(upload_file_url)
        # Specific enum coercion for known enum fields: always emit DB keys
        try:
            from enums import (
                AOIGeoType, DensificationLevel, DomainType,
                FaultDirection, InsituStressOption, InsituStressType,
                BackfillType, BackfillDelayRule, BackfillMaterial
            )
            enum_map = {
                # SlopeX & generic fields
                "pit_densification_intensity": DensificationLevel,
                "densification_intensity": DensificationLevel,
                "aoi_geo_type": AOIGeoType,
                # Domain
                "rock_soil": DomainType,
                "domain_type": DomainType,
                "domain_orientation": FaultDirection,
                # Fault
                "fault_direction": FaultDirection,
                "fault_material": DomainType,
                # Backfill
                "fill_type": BackfillType,
                "delay_rule": BackfillDelayRule,
                "elasticity": BackfillMaterial,
                # Insitu Stress
                "stress_option": InsituStressOption,
                # Insitu Stress Detail
                "name": InsituStressType,
            }
            for field_name, enum_cls in enum_map.items():
                if field_name in data:
                    member = parse_enum(enum_cls, data[field_name])
                    if member is not None:
                        # Direction fields should be single-letter
                        if field_name.endswith("_direction"):
                            data[field_name] = member.value[0].upper()
                        else:
                            data[field_name] = member.value
        except ImportError:
            pass
        # Strip any empty containers
        return strip_empty_fields(data)
    