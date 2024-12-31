import base64
import logging
import os
from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel

SKIP_DIRS = [
    ".vs",
    ".idea",
    ".git",
    ".vscode",
    ".angular",
    "node_modules",
    "bin",
    "obj",
    ".gradle",
    "build",
    "target",
    "dist",
    "venv",
    "__pycache__",
    ".pytest_cache",
]

# NOTE: casing does not matter here, as we use lower() in the check
REFERENCE_FILE_DIRS = [
    "Content",
    "Scripts",
]

BINARY_FILE_EXTENSIONS = [
    ".dll",  # Dynamic Link Library
    ".exe",  # Windows Executable Files
    ".bin",  # Generic Binary Files
    ".o",
    ".obj",  # Object Files
    ".zip",
    ".tar",
    ".rar",
    ".7z",  # Archive Files
    ".png",
    ".jpg",
    ".gif",
    ".bmp",
    ".tiff",  # Image Files
    ".mdb",  # Microsoft Access Database Files
    ".db",  # SQLite Database Files
    ".mp3",
    ".wav",  # Audio Files
    ".mp4",
    ".avi",
    ".mov",  # Video Files
    ".pdf",  # PDF Documents
    ".so",  # Shared Object Files in Unix/Linux
    ".dylib",  # Dynamic Library Files in macOS
    ".ttf",
    ".otf",  # Font Files
    ".accdb",  # Access Database Files
    ".ico",
    ".lock",  # e.g. cargo.lock, package-lock.json
    "-lock.json",
    ".lock.json",
    ".lockfile",
    ".lockfile.json",
]


class CodeFile(BaseModel):
    file_name: str
    source_code: str = ""

    def __lt__(self, other):
        return self.file_name < other.file_name


class CodeProject(BaseModel):
    display_name: str = ""
    source_language: str = ""
    files: List[CodeFile] = []
    reference_files: List[CodeFile] = []

    def __str__(self):
        s = f"Project folder: {self.display_name}\n"
        s += "Code files:\n"
        for file in self.files:
            s += file.file_name + "\n"
            s += "```\n"
            s += file.source_code + "\n"
            s += "```\n"
        return s

    def add_file(self, file_name: str, source_code: str):
        for f in self.files:
            if f.file_name == file_name:
                logging.warning(f"Overwriting file {file_name}")
                f.source_code = source_code
                return
        self.files.append(CodeFile(file_name=file_name, source_code=source_code))

    def remove_file(self, file_name: str) -> bool:
        n_files_before = len(self.files)
        self.files = [f for f in self.files if f.file_name != file_name]
        n_files_after = len(self.files)
        success = n_files_before != n_files_after
        if not success:
            logging.warning(f"Could not remove file {file_name}")
        return success

    def add_reference_file(self, file_name: str, source_code: str):
        for f in self.reference_files:
            if f.file_name == file_name:
                logging.warning(f"Overwriting reference file {file_name}")
                f.source_code = source_code
                return
        self.reference_files.append(
            CodeFile(file_name=file_name, source_code=source_code)
        )

    def remove_reference_file(self, file_name: str) -> bool:
        n_files_before = len(self.reference_files)
        self.reference_files = [
            f for f in self.reference_files if f.file_name != file_name
        ]
        n_files_after = len(self.reference_files)
        success = n_files_before != n_files_after
        if not success:
            logging.warning(f"Could not remove reference file {file_name}")
        return success

    def get_file(self, file_name: str) -> Optional[CodeFile]:
        for file in self.files:
            if file.file_name == file_name:
                return file
        return None

    def save_to_dir(self, project_base_dir: str):
        # check duplicate files in files and reference_files
        reference_file_names = [f.file_name for f in self.reference_files]
        file_names = [f.file_name for f in self.files]
        duplicates = set(reference_file_names) & set(file_names)
        if duplicates:
            logging.warning(
                f"Duplicate files in files and reference_files: {duplicates}"
            )
            logging.warning("This can cause wild behavior in the code execution.")

        os.makedirs(project_base_dir, exist_ok=True)
        # save ref files first, so that main files can overwrite duplicates
        for code_file in self.reference_files + self.files:
            try:
                # need normpath here because file_names can be created by linux container
                # and then used on windows container (code_executor)
                file_name = os.path.normpath(code_file.file_name)
                # make new dir if necessary
                if os.sep in file_name:
                    os.makedirs(
                        os.path.join(project_base_dir, os.path.dirname(file_name)),
                        exist_ok=True,
                    )
                if CodeProject._is_binary_file(file_name):
                    # Try to decode the source_code from base64
                    content = base64.b64decode(code_file.source_code)
                    mode = "wb"
                    encoding = None
                else:
                    # If it can't be decoded from base64, treat it as text
                    content = code_file.source_code
                    mode = "w"
                    encoding = "utf-8"
                with open(
                    os.path.join(project_base_dir, file_name),
                    mode,
                    encoding=encoding,
                ) as f:
                    f.write(content)
            except Exception as e:
                logging.error(f"Error saving file {file_name}: {e}")

    @staticmethod
    def _is_binary_file(file_path):
        _, ext = os.path.splitext(file_path)
        if ext == "":
            return True
        if ext.lower() in BINARY_FILE_EXTENSIONS:
            return True
        if "." not in os.path.basename(file_path):
            return True
        return False

    @staticmethod
    def _read_file_content(file_path, binary) -> Optional[str]:
        try:
            mode = "rb" if binary else "r"
            encoding = None if binary else "utf-8"
            with open(file_path, mode, encoding=encoding) as f:
                content = f.read()
                # remove BOM
                if not binary and content.startswith("\ufeff"):
                    content = content[1:]
            if binary:
                return base64.b64encode(content).decode()
            else:
                return content
        except UnicodeDecodeError:
            logging.error(f"UnicodeDecodeError for {file_path}, trying windows-1250")
            try:
                with open(file_path, "r", encoding="windows-1250") as f:
                    return f.read()
            except Exception as e:
                logging.error(
                    f"Error reading file {file_path} with windows-1250 encoding: {e}"
                )
            logging.error(f"UnicodeDecodeError for {file_path}, trying ISO-8859-1")
            try:
                with open(file_path, "r", encoding="ISO-8859-1") as f:
                    return f.read()
            except Exception as e:
                logging.error(
                    f"Error reading file {file_path} with ISO-8859-1 encoding: {e}"
                )
            return None
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return None

    @staticmethod
    def load_from_dir(display_name, base_dir, source_language) -> "CodeProject":
        files: list[CodeFile] = []
        reference_files: list[CodeFile] = []

        # load all files
        for root, _, filenames in os.walk(base_dir):
            if any(
                root.lower().endswith(os.sep + skip_dir)
                or (os.sep + skip_dir + os.sep) in root.lower()
                for skip_dir in SKIP_DIRS
            ):
                continue
            is_reference = False
            if any(
                root.lower().endswith(os.sep + ref_dir.lower())
                or (os.sep + ref_dir.lower() + os.sep) in root.lower()
                for ref_dir in REFERENCE_FILE_DIRS
            ):
                is_reference = True

            for filename in filenames:
                file_path = os.path.join(root, filename)
                binary = CodeProject._is_binary_file(file_path)
                content = CodeProject._read_file_content(file_path, binary)
                if content is not None:
                    relative_path = os.path.relpath(file_path, base_dir)
                    # Replace Windows path separators with Linux ones
                    relative_path = relative_path.replace("\\", "/")
                    if binary or is_reference:
                        reference_files.append(
                            CodeFile(file_name=relative_path, source_code=content)
                        )
                    else:
                        files.append(
                            CodeFile(file_name=relative_path, source_code=content)
                        )

        return CodeProject(
            display_name=display_name,
            files=files,
            reference_files=reference_files,
            source_language=source_language,
        )

    def split_reference_files(self, relative_path_to_main_csproj):
        # For C# projects, we need to distinguish between source files and reference files
        # files that are in the same directory or subdirectories as the main csproj are source files
        # all other files are reference files (additional files necessary for compilation)

        # get base dir of csproj file
        csproj_base_dir = os.path.dirname(relative_path_to_main_csproj)
        base_dir = os.path.join(csproj_base_dir, "")
        # Replace Windows path separators with Linux ones
        base_dir = base_dir.replace("\\", "/")

        source_files = []
        reference_files = []
        for f in self.files:
            if f.file_name.startswith(os.path.join(base_dir, "")):
                source_files.append(f)
            else:
                reference_files.append(f)

        self.files = source_files
        self.reference_files = reference_files


@dataclass
class ExecutionResult:
    project: CodeProject = None
    success: bool = False
    error: str = ""
    total_tests: int = -1
    passed_tests: int = -1
    failed_tests: int = 100
    test_output: str = ""
    runtime: float = -1
