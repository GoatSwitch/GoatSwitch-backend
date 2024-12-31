import os
import tempfile

from gs_common.file_ops import (
    backup_dict,
)


def test_backup_dict():
    # Arrange
    dict_to_save = {"key": "value"}

    with tempfile.TemporaryDirectory() as save_base_dir:
        with tempfile.TemporaryDirectory() as backup_base_dir:
            save_dir = os.path.join(save_base_dir, "generated", "guid")

            # Act
            backup_dict(dict_to_save, backup_base_dir, save_dir)

            # Assert
            assert os.path.exists(os.path.join(backup_base_dir, "guid", "backup.json"))


def test_backup_dict_multiple():
    # Arrange
    dict_to_save = {"key": "value"}
    dict_to_save2 = {"key2": "value2"}
    save_dir_2_suffix = "myfolder"

    with tempfile.TemporaryDirectory() as save_base_dir:
        with tempfile.TemporaryDirectory() as backup_base_dir:
            save_dir = os.path.join(save_base_dir, "generated", "guid")

            # Act
            backup_dict(dict_to_save, backup_base_dir, save_dir)

            # backup second
            backup_dict(dict_to_save2, backup_base_dir, save_dir + save_dir_2_suffix)

            # Assert
            assert os.path.exists(
                os.path.join(backup_base_dir, "guid" + save_dir_2_suffix, "backup.json")
            )

            # assert first still exists
            assert os.path.exists(os.path.join(backup_base_dir, "guid", "backup.json"))
