"""
Drone Odyssey Field Creator Module Package
แพ็คเกจสำหรับสร้างสนามแข่งขัน Drone Odyssey Challenge
"""

from .field_manager import FieldManager
from .field_config import FieldConfig

__version__ = "1.0.0"
__author__ = "Drone Odyssey Team"

# Export หลักของ package
__all__ = [
    'FieldManager',
    'FieldConfig'
]
