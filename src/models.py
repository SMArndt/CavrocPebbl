from datetime import datetime
from typing import List, Optional, TypedDict

from pydantic import (BaseModel, ConfigDict, Field, field_validator,
                      model_validator)

#from .bubble_base import BubbleBaseModel, parse_enum
from bubble_base import BubbleBaseModel, parse_enum
#from .enums import (AOIGeoType, AppType, BackfillDelayRule, BackfillMaterial,
from enums import (AOIGeoType, AppType, BackfillDelayRule, BackfillMaterial,
                    BackfillType, DensificationLevel, DomainType,
                    FaultDirection, FLACVersion, InsituStressOption,
                    InsituStressType, ProjectType, RelGeoAccuracy)

# Explicit imports (replace wildcard imports)
# from .bubble_base import *
# from .enums import *



#
# --- RocBox Utility ---
#
class ApiResponse(TypedDict, total=False):
    id: str
    created_at: str
    error: Optional[str]


#
# --- RocBox Input Model ---
#
class RocBoxInput(BaseModel):
    project_name: str
    file_format: str
    incl_actual_recon: bool = False
    first_row: int = 1
    last_row: int = 100
    recon_file_name: str = "default.csv"
    recon_accuracy: float = 1.0
    northwall_approximate_DD: float = 0.0
    Hangingwall_approximate_DD: float = 90.0
    crown_Dip: float = 10.0
    Floor_Dip: float = 10.0

    include_model_recon: bool = False
    first_step: int = 0
    last_step: int = 0
    stope_names_file: str = ""
    model_northwall_DD: float = 0.0
    model_hangingwall_DD: float = 0.0
    model_crown_Dip: float = 0.0
    model_floor_DD: float = 0.0
    search_distance: float = 0.0
    group_name_material1: str = ""
    group_name_material2: str = ""
    strain_limit_overbreak_material1: float = 0.0
    strain_limit_overbreak_material2: float = 0.0
    velocity_limit_overbreak: float = 0.0
    strain_limit_underbreak: float = 0.0

    include_lodes: bool = False
    stope_lodes_file: str = ""
    include_method: bool = False
    stope_method_file: str = ""
    include_directions: bool = False
    stope_direction_file: str = ""
    export_wall_surfaces: bool = False
    export_split_OB_north: bool = False
    export_split_OB_east: bool = False
    export_split_OB_west: bool = False
    export_split_OB_south: bool = False
    export_split_OB_crown: bool = False

    include_geom: bool = False

    model_config = ConfigDict(populate_by_name=True)



#
# --- Models Based on JSON Responses ---
#
class SlopeXModelConstruction(BubbleBaseModel):
    _id: Optional[str] = None
    name: str = ""
    modified_date: Optional[datetime] = Field(default=None, alias="Modified Date")
    created_date: Optional[datetime] = Field(default=None, alias="Created Date")
    created_by: Optional[str] = Field(default=None, alias="Created By")

    pit_densification_intensity: Optional[DensificationLevel] = None
    pit_densification_distance: float = 0.0
    pit_waste_dump_cohesion: float = 0.0
    pit_is_waste_dump_stage: bool = False
    pit_additional_solving_cycle: int = 0
    pit_srf_calculation: bool = False
    pit_vertical_excavation_distance: float = 0.0
    pit_waste_dump_density: float = 0.0
    pit_waste_dump_e: float = 0.0
    pit_immediate_excavation: bool = False
    pit_inc_groundwater: bool = False
    pit_waste_dump_friction_angle: float = 0.0
    pit_gradual_excavation: bool = False
    pit_upload: Optional[str] = None
    pit_included: bool = False
    topo_inc_pre_mine_topo: bool = False
    topo_inc_groundwater_table: bool = False
    topo_upload_file: Optional[str] = None
    topo_upload_phreatic_surface: Optional[str] = None
    pit_upload_phreatic_surface: Optional[str] = None

    aoi_geo_type: Optional[AOIGeoType] = None
    aoi_inc_aoi: bool = False
    aoi_densification_distance: float = 0.0
    aoi_upload: Optional[str] = None
    aoi_zone_edge_length: float = 0.0

    densification_intensity: Optional[DensificationLevel] = None
    fault_global_preset: Optional[List[float]] = None

    model_config = ConfigDict(populate_by_name=True)

    class Meta:
        file_fields = [
            "aoi_upload",
            "topo_upload_file",
            "topo_upload_phreatic_surface",
            "pit_upload",
            "pit_upload_phreatic_surface",
        ]

    @model_validator(mode="before")
    @classmethod
    def pre_validate_enum_and_patch(cls, values: dict):
        # Patch logic for fallback
        if (
            "pit_densification_intensity" not in values
            and "densification_intensity" in values
            and values["densification_intensity"] not in [None, "", "notfound"]
        ):
            values["pit_densification_intensity"] = values["densification_intensity"]

        # Enum conversion
        enum_fields = {
            "aoi_geo_type": AOIGeoType,
            "densification_intensity": DensificationLevel,
            "pit_densification_intensity": DensificationLevel,
        }
        for field_name, enum_cls in enum_fields.items():
            if field_name in values:
                try:
                    values[field_name] = parse_enum(enum_cls, values[field_name])
                except Exception:
                    # Let Pydantic handle invalid enum values with its own validation later
                    pass

        return values

    @field_validator(
        "pit_upload",
        "topo_upload_file",
        "topo_upload_phreatic_surface",
        "pit_upload_phreatic_surface",
        "aoi_upload",
        mode="before",
    )
    def strip_files(cls, v):
        from utils import extract_filename_from_url

        return extract_filename_from_url(v)


class SettingModel(BubbleBaseModel):
    _id: str
    file_format: str = ""
    slopeX_include_SRF: bool = False
    target_zones: int = 0

    import_map3D: bool = False
    import_map3D_file: Optional[str] = Field(default=None, alias="Map3D_file")

    FLAC_version: Optional[FLACVersion] = None
    GEM4D_output: bool = False
    inc_mXrap_result: bool = False

    import_mesh: bool = Field(default=False, alias="import_mesh")
    import_mesh_dir: str = ""
    import_mesh_file: Optional[str] = Field(default=None, alias="Mesh_import_filename")

    farfieldzonesize: int = 0
    paraview: bool = False
    predefined_zonesize: bool = False
    zonesize_dropdown: Optional[str] = None  # option set
    model_boundary_offset: int = 0
    save_dir: str = ""

    zone_size_number: Optional[float] = Field(default=None, alias="zone size number")
    zone_size_numbers: Optional[List[float]] = Field(
        default_factory=list, alias="zone size numbers"
    )

    slopeX_velocity_threshold: float = 0.0
    slopeX_displacement_threshold: float = 0.0
    slopeX_Max_Reduction_Factor: float = 0.0
    slopeX_SRF_Calc_increments: float = 0.0

    output_text: List[str] = Field(default_factory=list)

    created_date: Optional[datetime] = Field(
        default=None, alias="Created Date", exclude=True
    )
    modified_date: Optional[datetime] = Field(
        default=None, alias="Modified Date", exclude=True
    )
    created_by: Optional[str] = Field(default=None, alias="Created By", exclude=True)
    model_config = ConfigDict(populate_by_name=True)

    class Meta:
        file_fields = ["import_map3D_file", "import_mesh_file"]

    @field_validator("zone_size_number", mode="before")
    def validate_zone_size_number(cls, v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator("import_map3D_file", "import_mesh_file", mode="before")
    def validate_file_fields(cls, v):
        from utils import extract_filename_from_url

        return extract_filename_from_url(v)

    @field_validator("import_mesh", mode="before")
    def convert_yes_no_to_bool(cls, v):
        if isinstance(v, str):
            return v.lower() == "yes"
        return v

    @field_validator("FLAC_version", mode="before")
    def parse_flac_version(cls, v):
        # Allow human-readable labels (e.g. "7.0") to map to FLACVersion
        from bubble_base import parse_enum

        if v is None or isinstance(v, FLACVersion):
            return v
        # parse_enum returns an enum or None
        parsed = parse_enum(FLACVersion, v)
        return parsed or v


class ModelConstructionModel(BubbleBaseModel):
    _id: str

    topo_enabled: bool = False
    dev_enabled: bool = False
    hist_enabled: bool = False
    aoi_enabled: bool = False
    stoping_enabled: bool = False

    ground_surface_elevation: Optional[float] = 0.0
    model_construction_detail: List[str] = Field(
        default_factory=list, alias="model construction detail"
    )

    include_topography: Optional[str] = None
    include_area_of_interest: Optional[str] = None
    include_development: Optional[str] = None
    include_historical_mining: Optional[str] = None

    created_date: Optional[datetime] = Field(default=None, alias="Created Date")
    modified_date: Optional[datetime] = Field(default=None, alias="Modified Date")
    created_by: Optional[str] = Field(default=None, alias="Created By")

    @model_validator(mode="after")
    def set_include_flags(cls, values):
        values.include_topography = "yes" if values.topo_enabled else "no"
        values.include_area_of_interest = "yes" if values.aoi_enabled else "no"
        values.include_development = "yes" if values.dev_enabled else "no"
        values.include_historical_mining = "yes" if values.hist_enabled else "no"
        return values

    model_config = ConfigDict(populate_by_name=True)


class ModelConstructionDetail(BubbleBaseModel):
    _id: str

    file: Optional[str] = Field(default=None)
    zone_dens_dist: Optional[float] = Field(default=None)
    min_zonesize: Optional[float] = Field(default=None)
    init_zonesize: Optional[float] = Field(default=None)
    geometry_accuracy: Optional[RelGeoAccuracy] = Field(default=None)
    name: Optional[str] = Field(default=None)  # option set
    output_text: List[str] = Field(default_factory=list)

    created_date: Optional[datetime] = Field(alias="Created Date", default=None)
    modified_date: Optional[datetime] = Field(alias="Modified Date", default=None)
    created_by: Optional[str] = Field(alias="Created By", default=None)

    model_config = ConfigDict(populate_by_name=True)

    class Meta:
        file_fields = ["file"]

    @field_validator("geometry_accuracy", mode="before")
    def map_geometry_accuracy(cls, v):
        """
        Normalize various representations (int code, enum, or string) to RelGeoAccuracy.
        """
        from bubble_base import parse_enum

        # Use parse_enum to handle int codes (mapping by order), enum names, values, and labels
        parsed = parse_enum(RelGeoAccuracy, v)
        return parsed

    @field_validator("file", mode="before")
    def strip_file_urls(cls, v):
        from utils import extract_filename_from_url

        return extract_filename_from_url(v)


class BackfillModel(BubbleBaseModel):
    id: str = Field(alias="_id")
    slug: Optional[str] = Field(alias="Slug", default=None)

    backfill_cohesion: Optional[float] = None
    backfill_density: Optional[float] = None
    backfill_Ei: Optional[float] = None
    backfill_frictionangle: Optional[float] = None
    backfill_numsteps_delayed: Optional[float] = None
    backfill_numsteps: Optional[float] = None
    backfill_tension: Optional[float] = None
    backfill_poisson: Optional[float] = None

    index: int = Field(alias="index")

    backfill_default_text: str
    backfill_file: Optional[str] = None
    backfill_group_name: str
    backfill_indexname: str
    delay_rule_text: Optional[str] = None
    name: str

    backfill_output_text: List[str] = Field(default_factory=list)

    delay_multiplesteps: bool
    delayed_fill: bool = Field(alias="Delayed Fill")
    elastic: bool = Field(alias="Elastic")
    immediate_fill: bool = Field(alias="Immediate Fill")
    inelastic: bool = Field(alias="Inelastic")
    fileupload_new_backfill: bool = Field(alias="fileupload_new_backfill")
    visible: bool

    elasticity: Optional[BackfillMaterial] = Field(alias="Elasticity")
    # Represent backfill type and delay rule as Enum fields for validation
    fill_type: Optional[BackfillType] = Field(alias="Fill type", default=None)
    delay_rule: Optional[BackfillDelayRule] = Field(alias="delay_rule", default=None)

    created_date: Optional[datetime] = Field(alias="Created Date")
    modified_date: Optional[datetime] = Field(alias="Modified Date")
    created_by: Optional[str] = Field(alias="Created By")

    model_config = ConfigDict(populate_by_name=True)

    class Meta:
        file_fields = ["backfill_file"]
        # Override enum serialization: emit numeric_value for Bubble option-sets
        enum_overrides = {
            # Emit numeric IDs (1,2) for Bubble
            "fill_type": "numeric",
            "delay_rule": "numeric",
            # For elasticity enum, use human-readable label
            "elasticity": "str",
        }

    @field_validator("backfill_file", mode="before")
    @classmethod
    def strip_file_urls(cls, v):
        from utils import extract_filename_from_url

        if isinstance(v, dict):
            v = v.get("url") or v.get("id") or ""

        return extract_filename_from_url(v)

    @field_validator("fill_type", mode="before")
    def map_fill_type(cls, v):
        """
        Normalize fill_type input to BackfillType Enum instance.
        Accepts Enum, int, or string, and returns corresponding BackfillType.
        """
        if isinstance(v, BackfillType):
            return v
        mapping = {
            1: BackfillType.ImmediateFill,
            "1": BackfillType.ImmediateFill,
            "Immediate Fill": BackfillType.ImmediateFill,
            "immediate_fill": BackfillType.ImmediateFill,
            2: BackfillType.DelayedFill,
            "2": BackfillType.DelayedFill,
            "Delayed Fill": BackfillType.DelayedFill,
            "delayed_fill": BackfillType.DelayedFill,
        }
        return mapping.get(v)

    @field_validator("delay_rule", mode="before")
    def map_delay_rule(cls, v):
        """
        Normalize delay_rule input to BackfillDelayRule Enum instance.
        Accepts Enum, int, or string, and returns corresponding BackfillDelayRule.
        """
        if isinstance(v, BackfillDelayRule):
            return v
        mapping = {
            1: BackfillDelayRule.DelayByNumberOfMiningSteps,
            "1": BackfillDelayRule.DelayByNumberOfMiningSteps,
            "Delay by number of mining steps": BackfillDelayRule.DelayByNumberOfMiningSteps,
            "delay_by_number_of_mining_steps_delayed_based_on_the_mining_step_to_fill": BackfillDelayRule.DelayByNumberOfMiningSteps,
            2: BackfillDelayRule.DelayedBasedOnMiningStep,
            "2": BackfillDelayRule.DelayedBasedOnMiningStep,
            "Delayed based on the mining step to fill": BackfillDelayRule.DelayedBasedOnMiningStep,
            "delayed_based_on_the_mining_step_to_fill": BackfillDelayRule.DelayedBasedOnMiningStep,
        }
        return mapping.get(v)

    @field_validator("elasticity", mode="before")
    def map_elasticity(cls, v):
        if isinstance(v, BackfillMaterial):
            return v
        if isinstance(v, str) and v.lower() in {"elastic", "inelastic"}:
            return BackfillMaterial[v.capitalize()]
        return None


class FaultModel(BubbleBaseModel):
    _id: str
    created_by: str = Field(alias="Created By")
    created_date: Optional[datetime] = Field(alias="Created Date")
    modified_date: Optional[datetime] = Field(alias="Modified Date")

    fault_name: str
    fault_index: int
    fault_visible: Optional[bool] = None

    fault_assignorientations: Optional[bool] = None
    fault_inc_aniso: Optional[bool] = None

    fault_cohesion: Optional[float] = None
    fault_cohres: Optional[float] = None
    fault_critred: Optional[float] = None
    fault_density: Optional[float] = None
    fault_dialation_angle: Optional[float] = None
    fault_disfac: Optional[int] = None
    fault_Ei: Optional[int] = None
    fault_fricres: Optional[float] = None
    fault_friction_angle: Optional[int] = None
    fault_GSI: Optional[int] = None
    fault_miMax: Optional[float] = None
    fault_mimin: Optional[float] = None
    fault_normal_stiffness: Optional[int] = None
    fault_poisson: Optional[float] = None
    fault_shear_stiffness: Optional[int] = None
    fault_sigci: Optional[int] = None
    fault_stiffness_softening: Optional[bool] = None
    fault_tenres: Optional[float] = None
    fault_tension: Optional[float] = None

    fault_file: Optional[str] = None
    fault_surfacefile: Optional[str] = None
    fault_group_name: Optional[str] = None
    fault_default_text: Optional[str] = None
    fault_output_text: List[str] = Field(default_factory=list)
    fileupload_new_fault: Optional[bool] = None

    anisoDip: Optional[int] = Field(alias="AnisoDip", default=None)
    fault_AnisoDipD: Optional[int] = Field(default=None)
    fault_AnisoFac: Optional[float] = None

    fault_direction: Optional[FaultDirection] = Field(
        default=None, alias="fault_direction"
    )
    fault_material: Optional[DomainType] = Field(default=None, alias="fault_material")

    model_config = ConfigDict(populate_by_name=True)

    class Meta:
        file_fields = ["fault_file", "fault_surfacefile"]
        enum_overrides = {"fault_direction": "letter", "fault_material": "str"}

    @field_validator("fault_direction", mode="before")
    def map_fault_direction(cls, v):
        if not v:
            return FaultDirection.top
        v = v.strip()
        if len(v) == 1:
            letter_map = {d.letter: d for d in FaultDirection}
            return letter_map.get(v.upper(), FaultDirection.top)
        try:
            return FaultDirection(v.capitalize())
        except Exception:
            return FaultDirection.top

    @field_validator("fault_material", mode="before")
    def map_fault_material(cls, v):
        if isinstance(v, str):
            if v.lower() == "soil":
                return DomainType.Soil
            elif v.lower() == "rock":
                return DomainType.Rock
        if isinstance(v, int):
            return DomainType(v)
        return DomainType.Rock

    @field_validator("fault_surfacefile", "fault_file", mode="before")
    def strip_file_urls(cls, v):
        from utils import extract_filename_from_url

        return extract_filename_from_url(v)


class DomainModel(BubbleBaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_by: Optional[str] = Field(default=None, alias="Created By")
    created_date: Optional[datetime] = Field(default=None, alias="Created Date")
    modified_date: Optional[datetime] = Field(default=None, alias="Modified Date")

    anisotropic: Optional[bool] = Field(default=False)
    assign_orientations: Optional[bool] = Field(
        default=False, alias="assign orientations"
    )
    cohres: Optional[float] = Field(default=0.01)
    critred: Optional[float] = Field(default=0.5)
    density: Optional[float] = Field(default=2.7, alias="density")  # Default to 2.7
    disFac: Optional[float] = Field(
        default=0.0, alias="disFac"
    )  # Default D-factor to 0.0
    domain_name: Optional[str] = Field(default=None, alias="domain name")
    ei: Optional[float] = Field(default=20000.0)
    fricres: Optional[float] = Field(default=30.0)  # Default to 30
    linear_elastic: Optional[bool] = (
        False  # Changed from required to optional with default False
    )
    miMax: Optional[float] = Field(default=10.0, alias="miMax")  # Default to 10
    miMin: Optional[float] = Field(default=5.0, alias="miMin")  # Default to 5
    sigci: Optional[float] = Field(default=100.0, alias="UCS")  # Default to 100
    tenres: Optional[float] = Field(
        default=0.0, alias="residual tension"
    )  # Default to 0
    gsi: Optional[float] = Field(default=70.0, alias="GSI")  # Default to 70
    friction_angle: Optional[float] = Field(default=32.0, alias="friction angle")
    tension: Optional[float] = Field(default=0.02, alias="tension")
    dialation_angle: Optional[float] = Field(default=5.0, alias="dialation angle")
    cohesion: Optional[float] = Field(default=0.05, alias="cohesion")
    nu: Optional[float] = Field(default=0.25, alias="poissons ratio")

    domain_orientation: Optional[FaultDirection] = Field(
        default=FaultDirection.Top, alias="domain_orientation"
    )
    domain_type: DomainType = Field(alias="rock_soil", default=DomainType.Rock)
    rock_soil: Optional[DomainType] = Field(default=None, alias="rock soil")
    index: int
    default_text: Optional[str] = Field(default=None)
    domain_usr_title: Optional[str] = Field(default=None)
    output_text: List[str] = Field(default_factory=list)
    visible: bool = True
    domain_group_name: Optional[str] = None
    stiffness_softening: Optional[bool] = Field(
        default=False, alias="stiffness softening"
    )
    fileupload_new_domain: Optional[bool] = None
    domain_file: Optional[str] = None
    domain_surface_file: Optional[str] = None

    anisoDip: Optional[int] = Field(default=0, alias="anisoDip")  # Default to 0
    anisodipD: Optional[int] = Field(default=0, alias="anisodipD")  # Default to 0
    anisoFac: Optional[float] = Field(default=0.0, alias="anisoFac")  # Default to 2.0

    model_config = ConfigDict(populate_by_name=True)

    class Meta:
        file_fields = ["domain_file", "domain_surface_file"]
        enum_overrides = {"domain_orientation": "letter", "domain_type": "str"}

    @property
    def anisotropy_surface_normal_direction(self) -> str:
        return self.domain_orientation.value if self.domain_orientation else "T"

    @property
    def anisotropy_surface_normal_direction_letter(self) -> str:
        return self.domain_orientation.letter if self.domain_orientation else "T"

    @model_validator(mode="before")
    @classmethod
    def parse_domain_fields(cls, values):
        try:
            if "rock_soil" in values:
                values["rock_soil"] = parse_enum(DomainType, values["rock_soil"])

            # Handle linear_elastic properly:
            # 1. If missing, add it with default False
            # 2. If None or empty string, explicitly set to False
            if "linear_elastic" not in values:
                values["linear_elastic"] = False
            elif values["linear_elastic"] in [None, ""]:
                values["linear_elastic"] = False
        except Exception as e:
            # Log the error for debugging
            print(f"Error in parse_domain_fields: {e}")
            # Ensure linear_elastic is set
            values["linear_elastic"] = False
        # Default stiffness_softening based on material: yes for rock, no for soil
        try:
            if values.get("stiffness_softening") in (None, ""):
                mat = values.get("rock_soil")
                values["stiffness_softening"] = (
                    True if mat == DomainType.Rock else False
                )
        except Exception:
            values["stiffness_softening"] = False
        return values

    @field_validator("domain_type", mode="before")
    def map_domain_type(cls, v):
        if isinstance(v, DomainType):
            return v
        if isinstance(v, int):
            return (
                DomainType(v) if v in (1, 2) else DomainType.Rock
            )  # Defaulting to Rock if value is outside 1 or 2
        if isinstance(v, str):
            if v.lower() == "soil":
                return DomainType.Soil
            elif v.lower() == "rock":
                return DomainType.Rock
        return DomainType.Rock  # Default to Rock

    @field_validator("domain_orientation", mode="before")
    def map_domain_orientation(cls, v):
        if not v:
            return FaultDirection.Top
        v = v.strip()
        if len(v) == 1:
            return {d.letter: d for d in FaultDirection}.get(
                v.upper(), FaultDirection.Top
            )
        try:
            return FaultDirection(v.capitalize())
        except Exception:
            return FaultDirection.Top

    # @field_validator("domain_type", mode="before")
    # def map_domain_type(cls, v):
    #     if isinstance(v, DomainType):
    #         return v
    #     if isinstance(v, int):
    #         return DomainType(v) if v in (1, 2) else DomainType.Rock
    #     if isinstance(v, str):
    #         if v.lower() == "soil":
    #             return DomainType.Soil
    #         elif v.lower() == "rock":
    #             return DomainType.Rock
    #     return DomainType.Rock

    @field_validator("domain_file", "domain_surface_file", mode="before")
    def strip_file_urls(cls, v):
        from utils import extract_filename_from_url

        return extract_filename_from_url(v)


class InsituStressModel(BubbleBaseModel):
    _id: str
    created_date: Optional[datetime] = Field(
        default=None, alias="Created Date", exclude=True
    )
    modified_date: Optional[datetime] = Field(
        default=None, alias="Modified Date", exclude=True
    )
    created_by: Optional[str] = Field(default=None, alias="Created By", exclude=True)

    ground_surface_elevation: Optional[float] = None
    major_hori_vert_stressratio: Optional[float] = None
    minor_hori_vert_stressratio: Optional[float] = None
    orientation_maj_stress: Optional[float] = None
    insitustress_detail: List[str] = Field(
        default_factory=list, alias="insitu stress detail"
    )
    gndsrfc_elevation: Optional[bool] = Field(default=False)
    stress_option: Optional[InsituStressOption] = Field(default=None)

    @field_validator("stress_option", mode="before")
    def parse_stress_option(cls, v):
        # Allow human-readable or db_value strings to map to InsituStressOption
        from bubble_base import parse_enum

        if v is None:
            return None
        parsed = parse_enum(InsituStressOption, v)
        if parsed is None:
            raise ValueError(f"Invalid enum value '{v}' for InsituStressOption")
        return parsed


class InsituStressDetailModel(BubbleBaseModel):
    _id: str
    parent_stress: str
    name: Optional[InsituStressType]
    gradient: Optional[float]
    plunge: Optional[float]
    trend: Optional[float]
    locked_in: Optional[float] = Field(alias="locked in")
    output_text: Optional[List[str]] = Field(default_factory=list)

    created_by: Optional[str] = Field(default=None, alias="Created By")
    created_date: Optional[datetime] = Field(default=None, alias="Created Date")
    modified_date: Optional[datetime] = Field(default=None, alias="Modified Date")

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.lower()
        return super()._missing_(value)

    class Meta:
        enum_overrides = {
            "name": "value",
        }


class SolvingParameterModel(BubbleBaseModel):
    _id: str
    additional_cycles: Optional[int] = Field(default=0)
    first_step: Optional[int] = Field(default=0)
    solve_steps_number: Optional[int] = Field(default=0)
    total_mine_steps: Optional[int] = Field(default=0)
    output_text: List[str] = Field(default_factory=list)
    step_geometry: List[str] = Field(default_factory=list)

    created_date: Optional[datetime] = Field(
        default=None, alias="Created Date", exclude=True
    )
    modified_date: Optional[datetime] = Field(
        default=None, alias="Modified Date", exclude=True
    )
    created_by: Optional[str] = Field(default=None, alias="Created By", exclude=True)

    model_config = ConfigDict(populate_by_name=True)


class ProjectModel(BubbleBaseModel):
    _id: str
    project_name: str
    setting: Optional[str] = None
    insitu_stress: Optional[str] = Field(default=None, alias="insitu stress")
    solving_parameter: Optional[str] = Field(default=None, alias="solving parameter")

    all_created: bool = Field(False, alias="_all_created")
    project_linearelastic: bool = False
    include_faults: bool = False
    include_backfills: Optional[bool] = Field(default=False, alias="include_backfills")
    include_stress: bool = False

    simulations: List[str] = Field(default_factory=list, alias="_simulations")
    url_list: List[Optional[str]] = Field(default_factory=list, alias="_url_list")
    backfill: List[str] = Field(default_factory=list)
    cases_list: List[str] = Field(default_factory=list)
    fault: List[str] = Field(default_factory=list)
    rock_mass_domain: List[str] = Field(default_factory=list, alias="rock mass domain")
    SlopeX_Pit_Excavations: List[str] = Field(default_factory=list)
    output_text: List[str] = Field(default_factory=list)
    user: List[str] = Field(default_factory=list)

    input_file: Optional[str] = Field(default=None, alias="_input_file")
    fault_global_file: Optional[str] = None
    fault_global_preset: Optional[List[float]] = None
    fault_global_thickness: Optional[float] = None
    model_construction: Optional[str] = Field(alias="model construction", default=None)

    output_file: Optional[str] = Field(default=None)
    project_type: Optional[ProjectType] = Field(default=None)
    company: Optional[str] = Field(default=None)
    app_type: Optional[AppType] = None
    upload_file: Optional[str] = None
    slug: Optional[str] = Field(default=None, alias="Slug")

    created_date: Optional[datetime] = Field(default=None, alias="Created Date")
    modified_date: Optional[datetime] = Field(default=None, alias="Modified Date")
    created_by: Optional[str] = Field(default=None, alias="Created By")

    model_config = ConfigDict(populate_by_name=True)

    class Meta:
        file_fields = ["fault_global_file", "upload_file", "input_file"]

    @field_validator("fault_global_file", "upload_file", "input_file", mode="before")
    def strip_file_urls(cls, v):
        from utils import extract_filename_from_url

        return extract_filename_from_url(v)

    @field_validator("include_backfills", mode="before")
    def coerce_backfill_flag(cls, v):
        if isinstance(v, list):
            return len(v) > 0
        if isinstance(v, str):
            return v.strip().lower() == "yes"
        return bool(v)


#
# --- Composite Classes ---
#
class Stopex(BubbleBaseModel):
    """
    Aggregates: Project, Setting, Model Construction, Model Construction Detail,
    Backfill, Domain, Fault, plus optional Stress & SolvingParameter.
    """

    project: ProjectModel
    settings: SettingModel
    # model_construction: Optional[ModelConstructionModel] = None
    model_construction: ModelConstructionModel
    model_construction_details: List[ModelConstructionDetail] = Field(
        default_factory=list
    )
    backfills: List[BackfillModel]
    domains: List[DomainModel]
    faults: List[FaultModel]
    stress: Optional[InsituStressModel]
    stress_details: Optional[List[InsituStressDetailModel]]
    solving_parameter: Optional[SolvingParameterModel]

    def model_dump(self, *args, **kwargs):
        """Override model_dump to handle None for model_construction in SlopeX projects"""
        data = super().model_dump(*args, **kwargs)
        # For SlopeX projects, we'll still include model_construction as None
        # but remove model_construction_details if it's empty
        if not self.model_construction and not self.model_construction_details:
            data.pop("model_construction_details", None)
        return data

    def to_bubble_dict(self, upload_file_url: Optional[str] = None) -> dict:
        """
        Custom to_bubble_dict implementation to handle None model_construction.
        """
        from logging_config import logger

        # First get the standard dictionary
        data = super().to_bubble_dict(upload_file_url)

        # For SlopeX projects, remove model_construction fields if None
        if not self.model_construction:
            logger.info(
                "ℹ️ Removing model_construction key from bubble data since it's None"
            )
            data.pop("model_construction", None)

        if not self.model_construction_details:
            logger.info("ℹ️ Removing empty model_construction_details from bubble data")
            data.pop("model_construction_details", None)

        return data

    model_config = ConfigDict(populate_by_name=True)


class Slopex(BubbleBaseModel):
    """
    Aggregates: Project, Setting, SlopeX Model Construction, Domain, Fault, Stress, StressDetail,
    plus optional solving_parameter. Includes pit_excavations (list).
    """

    project: ProjectModel
    settings: SettingModel
    slopex_model_construction: SlopeXModelConstruction
    pit_excavations: List[SlopeXModelConstruction] = Field(default_factory=list)
    domains: List[DomainModel]
    host_domain: Optional[DomainModel] = None
    faults: List[FaultModel]
    stress: InsituStressModel
    stress_details: List[InsituStressDetailModel]
    solving_parameter: Optional[SolvingParameterModel] = None

    model_config = ConfigDict(populate_by_name=True)
