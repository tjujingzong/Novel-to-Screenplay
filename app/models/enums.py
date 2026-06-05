"""Enumeration types for the screenplay YAML schema."""

from enum import Enum


class RoleType(str, Enum):
    """Character role classification."""
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    MINOR = "minor"
    EXTRA = "extra"


class TimeOfDay(str, Enum):
    """Time of day for scene headings."""
    DAY = "DAY"
    NIGHT = "NIGHT"
    DAWN = "DAWN"
    DUSK = "DUSK"
    CONTINUOUS = "CONTINUOUS"
    LATER = "LATER"
    MOMENTS_LATER = "MOMENTS_LATER"


class IntExt(str, Enum):
    """Interior/Exterior designation for scene headings."""
    INT = "INT"
    EXT = "EXT"
    INT_EXT = "INT_EXT"
    EXT_INT = "EXT_INT"


class ElementType(str, Enum):
    """Types of elements within a scene."""
    ACTION = "action"
    DIALOGUE = "dialogue"
    PARENTHETICAL = "parenthetical"
    TRANSITION = "transition"
    NOTE = "note"


class TransitionType(str, Enum):
    """Types of scene transitions."""
    CUT_TO = "CUT_TO"
    FADE_OUT = "FADE_OUT"
    FADE_TO_BLACK = "FADE_TO_BLACK"
    DISSOLVE_TO = "DISSOLVE_TO"
    SMASH_CUT = "SMASH_CUT"
    MATCH_CUT = "MATCH_CUT"
    WIPE_TO = "WIPE_TO"
    INTERCUT = "INTERCUT"
    MONTAGE = "MONTAGE"
    TIME_LAPSE = "TIME_LAPSE"


class ScreenplayFormat(str, Enum):
    """Format type of the screenplay."""
    FEATURE_FILM = "feature_film"
    TV_EPISODE = "tv_episode"
    MINISERIES = "miniseries"
    SHORT_FILM = "short_film"


class ElementImportance(str, Enum):
    """Importance level of an action element."""
    KEY = "key"
    STANDARD = "standard"
    BACKGROUND = "background"


class ConversionStage(str, Enum):
    """Stages of the conversion pipeline."""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    SPLITTING = "splitting"
    EXTRACTING_CHARACTERS = "extracting_characters"
    CONVERTING = "converting"
    ASSEMBLING = "assembling"
    VALIDATING = "validating"
    COMPLETE = "complete"
    ERROR = "error"
