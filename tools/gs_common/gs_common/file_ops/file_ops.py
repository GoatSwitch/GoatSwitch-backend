import json
import logging
import os
import shutil
import threading
import time
import uuid
from datetime import datetime

from gs_common.tracing import current_trace_id

# NOTE: file_ops works with threads instead of async
# because shutil methods cannot be async


def generate_save_dir(service_name: str) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H-%M-%S")
    guid = uuid.uuid1().hex
    trace_id = current_trace_id.get()
    if "-" in trace_id:
        trace_id = trace_id.split("-")[1]
    # date / trace-id / service / time / guid
    return os.path.join(
        "generated",
        date,
        trace_id,
        service_name,
        time + "_" + guid,
    )


def backup_dict_in_background(dict_to_save: dict, backup_base_dir: str, save_dir: str):
    t = threading.Thread(
        target=backup_dict, args=(dict_to_save, backup_base_dir, save_dir)
    )
    t.start()


def backup_dict(dict_to_save: dict, backup_base_dir: str, save_dir: str):
    start_time = time.time()
    try:
        backup_dir = create_backup_dir(backup_base_dir, save_dir)
        save_file = os.path.join(backup_dir, "backup.json")
        with open(save_file, "w") as f:
            json.dump(dict_to_save, f, indent=2)
    except Exception as e:
        msg = f"Error while saving dict backup: {e}"
        logging.error(msg)
        logging.info(f"failed to backup dict: {dict_to_save}")
        raise Exception(msg)
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(
            f"backup_dict of save_dir({save_dir}) took {elapsed_time:.2f} seconds"
        )


def create_backup_dir(backup_base_dir: str, save_dir: str) -> str:
    if not os.path.exists(backup_base_dir):
        msg = f"Backup directory does not exist: {backup_base_dir}"
        logging.error(msg)
        raise Exception(msg)
    # save dir: generated/date/trace-id/service/time/guid
    # backup dir: /mnt/gs-vault/date/trace-id/service/time/guid
    save_dir_parts = os.path.normpath(save_dir).split(os.path.sep)
    if "generated" not in save_dir_parts:
        msg = f"Invalid save_dir (no generated dir found): {save_dir}"
        logging.error(msg)
        raise Exception(msg)

    tail = os.path.join(*save_dir_parts[save_dir_parts.index("generated") + 1 :])
    backup_dir = os.path.join(backup_base_dir, tail)
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir
