from gs_common.CodeProject import CodeProject
import logging


def get_loc_from_project(project: CodeProject) -> int:
    loc = 0
    for file in project.files:
        loc += file.source_code.count("\n")
    return loc


def log_user_metrics(
    projects: list[CodeProject], target_language: str, stage="input"
) -> None:
    if len(projects) == 0:
        return
    try:
        user_metrics = {
            f"{stage}loc": 0,
            f"{stage}numfiles": 0,
        }
        for project in projects:
            # lines of code
            user_metrics[f"{stage}loc"] += get_loc_from_project(project)
            # number of files
            user_metrics[f"{stage}numfiles"] += len(project.files)
        for k, v in user_metrics.items():
            logging.info(f"GSUSERMETRIC:{k}={v}")
    except Exception as e:
        logging.error(f"Error extracting user metrics: {e}")
