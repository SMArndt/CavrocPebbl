# enums.py
from enum import Enum, IntEnum

from bubble_base import BubbleEnum


class LabelledIntEnum(IntEnum):
    @property
    def label(self) -> str:
        """Return the human-readable label for Bubble option sets."""
        return str(self)


class LabelledStrEnum(str, Enum):
    @property
    def label(self) -> str:
        """Return the human-readable label for Bubble option sets."""
        return str(self)


class AOIGeoType(BubbleEnum):
    Surface = ("Surface", "surface")
    ClosedVolume = ("Closed Volume", "closed_volume")
    PitSlope = ("Pit Slope", "pit_stope")  # Bubble typo preserved

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class DensificationLevel(BubbleEnum):
    No = ("No Densification", "no_densification")
    Minimum = ("Minimum Densification", "minimum_densification")
    Intermediate = (
        "Intermediate Densification",
        "internmediate_densification",
    )  # Bubble typo preserved
    Maximum = ("Maximum Densification", "maximum_densification")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class FaultDirection(BubbleEnum):
    Top = ("Top", "top")
    Down = ("Down", "down")
    North = ("North", "north")
    South = ("South", "south")
    East = ("East", "east")
    West = ("West", "west")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj

    # Allow lowercase attribute access by db_value (e.g. FaultDirection.north)
    @classmethod
    def _alias_lowercase(cls):
        for member in cls:
            setattr(cls, member.value, member)

    # initialize aliases


_ = FaultDirection._alias_lowercase()


class BackfillDelayRule(BubbleEnum):
    DelayByNumberOfMiningSteps = (
        "Delay by number of mining steps",
        "delay_by_number_of_mining_steps_delayed_based_on_the_mining_step_to_fill",
    )
    DelayedBasedOnMiningStep = (
        "Delayed based on the mining step to fill",
        "delayed_based_on_the_mining_step_to_fill",
    )

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class BackfillMaterial(BubbleEnum):
    Elastic = ("Elastic", "elastic")
    Inelastic = ("Inelastic", "inelastic")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class BackfillType(BubbleEnum):
    ImmediateFill = ("Immediate Fill", "immediate_fill")
    DelayedFill = ("Delayed Fill", "delayed_fill")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class DomainType(BubbleEnum):
    Soil = ("Soil", "soil")
    Rock = ("Rock", "rock")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class InsituStressOption(BubbleEnum):
    Simple = ("Simple", "simple")
    Detailed = ("Detailed", "detailed")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class RelGeoAccuracy(BubbleEnum):
    Maximum = ("Maximum", "maximum")
    Intermediate = ("Intermediate", "intermediate")
    Minimum = ("Minimum", "minimum")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class FLACVersion(BubbleEnum):
    v5_0 = ("5.0", "5_0")
    v7_0 = ("7.0", "7_0")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class ProjectType(BubbleEnum):
    Lite = ("Lite", "lite")
    Pro = ("Pro", "pro")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class AppType(BubbleEnum):
    StopeX = ("stopex", "stopex")
    SlopeX = ("slopex", "slopex")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj


class ModelConstructionDetailName(str, Enum):
    """
    Option-set for model construction detail names.
    Stored value is the Bubble db_value; use .display() for human-readable labels.
    """

    Stoping = "stoping"
    Topography = "topo"
    Development = "development"
    AreaOfInterest = "area_of_interest"
    HistoricalMining = "historical_mining"
    PitExcavation = "pit_excavation"
    PreMiningTopography = "pre_mining_topography"

    @classmethod
    def from_display(cls, display: str) -> "ModelConstructionDetailName":
        """
        Reverse lookup from human-readable label to enum member.
        """
        mapping = {
            "Stoping": cls.Stoping,
            "Topography": cls.Topography,
            "Development": cls.Development,
            "Area of Interest": cls.AreaOfInterest,
            "Historical Mining": cls.HistoricalMining,
            "Pit Excavation": cls.PitExcavation,
            "Pre-Mining Topography": cls.PreMiningTopography,
        }
        try:
            return mapping[display]
        except KeyError:
            raise ValueError(
                f"Invalid display name for ModelConstructionDetailName: '{display}'"
            )

    def display(self) -> str:
        """
        Human-readable label for this enum member.
        """
        mapping = {
            self.Stoping.value: "Stoping",
            self.Topography.value: "Topography",
            self.Development.value: "Development",
            self.AreaOfInterest.value: "Area of Interest",
            self.HistoricalMining.value: "Historical Mining",
            self.PitExcavation.value: "Pit Excavation",
            self.PreMiningTopography.value: "Pre-Mining Topography",
        }
        return mapping.get(self.value, self.value)


class InsituStressType(BubbleEnum):
    Simple = ("Simple", "simple")
    Minimum = ("Minimum", "minimum")
    Intermediate = ("Intermediate", "intermediate")
    Maximum = ("Maximum", "maximum")

    def __new__(cls, label, db_value):
        obj = object.__new__(cls)
        obj._value_ = db_value
        obj.label = label
        return obj

    @classmethod
    def _missing_(cls, value):
        """
        Allow case-insensitive matching for InsituStressType values.
        """
        if isinstance(value, str):
            val = value.strip().lower()
            try:
                return cls(val)
            except ValueError:
                pass
        return super()._missing_(value)
