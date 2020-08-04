from pathlib import Path
from typing import Union, Tuple, cast

from yk_gmd_blender.structurelib.base import PackingValidationError
from yk_gmd_blender.yk_gmd.v2.abstract.gmd_scene import GMDScene
from yk_gmd_blender.yk_gmd.v2.converters.yk1.from_abstract import pack_abstract_contents_YK1
from yk_gmd_blender.yk_gmd.v2.converters.yk1.to_abstract import GMDAbstractor_YK1
from yk_gmd_blender.yk_gmd.v2.errors.error_classes import InvalidGMDFormatError
from yk_gmd_blender.yk_gmd.v2.errors.error_reporter import ErrorReporter
from yk_gmd_blender.yk_gmd.v2.structure.common.file import FileUnpackError
from yk_gmd_blender.yk_gmd.v2.structure.common.header import GMDHeaderStruct, GMDHeaderStruct_Unpack
from yk_gmd_blender.yk_gmd.v2.structure.endianness import check_is_file_big_endian
from yk_gmd_blender.yk_gmd.v2.structure.kenzan.file import FileData_Kenzan, FilePacker_Kenzan
from yk_gmd_blender.yk_gmd.v2.structure.version import GMDVersion, VersionProperties
from yk_gmd_blender.yk_gmd.v2.structure.yk1.file import FileData_YK1, FilePacker_YK1


def _get_file_data(data: Union[Path, str, bytes], error_reporter: ErrorReporter) -> bytes:
    if isinstance(data, (Path, str)):
        try:
            with open(data, "rb") as in_file:
                data = in_file.read()
            return data
        except FileNotFoundError as e:
            error_reporter.fatal(str(e))
    else:
        return data


def _extract_base_header(data: bytes) -> Tuple[bool, GMDHeaderStruct]:
    big_endian = True
    base_header, _ = GMDHeaderStruct_Unpack.unpack(big_endian, data=data, offset=0)
    big_endian = check_is_file_big_endian(base_header.file_endian_check)
    # Reimport the header with the correct endianness
    base_header, _ = GMDHeaderStruct_Unpack.unpack(big_endian, data=data, offset=0)
    return big_endian, base_header


def get_file_header(data: Union[Path, str, bytes], error_reporter: ErrorReporter) -> GMDHeaderStruct:
    data = _get_file_data(data, error_reporter)
    _, base_header = _extract_base_header(data)
    return base_header


def read_gmd_structures(data: Union[Path, str, bytes], error_reporter: ErrorReporter) -> Tuple[VersionProperties, Union[FileData_Kenzan, FileData_YK1]]:
    data = _get_file_data(data, error_reporter)
    big_endian, base_header = _extract_base_header(data)

    version_props = base_header.get_version_properties()
    if version_props.major_version == GMDVersion.Kiwami1:
        try:
            contents, _ = FilePacker_YK1.unpack(big_endian, data=data, offset=0)

            return version_props, contents
        except FileUnpackError as e:
            error_reporter.fatal(str(e))
    elif version_props.major_version == GMDVersion.Kenzan:
        try:
            contents, _ = FilePacker_Kenzan.unpack(big_endian, data=data, offset=0)

            return version_props, contents
        except FileUnpackError as e:
            error_reporter.fatal(str(e))
    else:
        raise InvalidGMDFormatError(f"File format version {version_props.version_str} is not readable")


def read_abstract_scene_from_filedata_object(version_props: VersionProperties, contents: Union[FileData_Kenzan, FileData_YK1], error_reporter: ErrorReporter) -> GMDScene:
    if version_props.major_version == GMDVersion.Kiwami1:
        return GMDAbstractor_YK1(version_props, cast(FileData_YK1, contents), error_reporter).make_abstract_scene()
    else:
        raise InvalidGMDFormatError(f"File format version {version_props.version_str} is not abstractable")


def read_abstract_scene(data: Union[Path, str, bytes], error_reporter: ErrorReporter) -> GMDScene:
    data = _get_file_data(data, error_reporter)

    version_props, file_data = read_gmd_structures(data, error_reporter)
    return read_abstract_scene_from_filedata_object(version_props, file_data, error_reporter)


def check_version_writeable(version_props: VersionProperties, error_reporter: ErrorReporter):
    if version_props.major_version == GMDVersion.Kiwami1:
        return
    else:
        error_reporter.fatal(f"File format version {version_props.version_str} is not writeable")


def write_abstract_scene_out(version_props: VersionProperties, file_is_big_endian: bool, vertices_are_big_endian: bool,
                             scene: GMDScene, path: Union[Path, str], error_reporter: ErrorReporter):
    if version_props.major_version == GMDVersion.Kiwami1:
        file_data = pack_abstract_contents_YK1(version_props, file_is_big_endian, vertices_are_big_endian, scene, error_reporter)

        try:
            data_bytearray = bytearray()
            FilePacker_YK1.pack(file_data.file_is_big_endian(), file_data, data_bytearray)

            with open(path, "wb") as out_file:
                out_file.write(data_bytearray)
        except (PackingValidationError, IOError) as e:
            error_reporter.fatal(str(e))
    else:
        raise InvalidGMDFormatError(f"File format version {version_props.version_str} is not writeable")
