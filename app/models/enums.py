import enum

class HardwareStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    REPAIR = "repair"
    UNKNOWN = "unknown" 