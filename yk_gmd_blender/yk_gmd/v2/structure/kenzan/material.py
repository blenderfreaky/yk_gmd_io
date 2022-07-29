from dataclasses import dataclass
from typing import List

from yk_gmd_blender.structurelib.base import StructureUnpacker, FixedSizeArrayUnpacker
from yk_gmd_blender.structurelib.primitives import *
from yk_gmd_blender.yk_gmd.v2.structure.common.material_base import MaterialBaseStruct


@dataclass(frozen=True)
class MaterialStruct_Kenzan(MaterialBaseStruct):
    diffuse: List[int]
    opacity: float
    specular: List[int]
    ambient: List[int]
    emissive: float

    power: float
    intensity: float

    padding: int


MaterialStruct_Kenzan_Unpack = StructureUnpacker(
    MaterialStruct_Kenzan,
    fields=[
        # TODO: These two are probs wrong
        ("power", c_float16),
        ("intensity", c_float16),

        ("diffuse", FixedSizeArrayUnpacker(c_uint8, 3)),
        ("padding", c_uint8),

        ("specular", FixedSizeArrayUnpacker(c_uint8, 3)),
        ("opacity", c_unorm8),

        ("ambient", FixedSizeArrayUnpacker(c_uint8, 3)),
        ("emissive", c_unorm8)

    ]
)
