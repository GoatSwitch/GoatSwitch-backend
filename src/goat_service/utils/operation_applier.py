import copy
import difflib
import logging
import os
import re
from textwrap import dedent

from gs_common.CodeProject import CodeProject
from gs_common.tracing import current_company_id
from pydantic import BaseModel

OP_USAGE = """
1. Generate a rough plan of the changes you need to make to the source code to meet the user requirements.
2. Follow the plan and generate edits for the source code files (*SEARCH/REPLACE* blocks) to meet the user requirements. The edits will be applied to the source code files in the order they are generated.

You can make edits via *SEARCH/REPLACE* blocks.
Every *SEARCH/REPLACE block* must use this format:
1. The file path relative to the project folder alone on a line, verbatim. No bold asterisks, no quotes around it, no escaping of characters, etc.
2. The start of search block: <<<< SEARCH
3. A contiguous chunk of lines to search for in the existing source code
4. The dividing line: ====
5. A contiguous chunk of lines to replace the search block with
6. The end of the replace block: >>>> REPLACE

Example:
Services/MyService.cs
<<<< SEARCH
using System;
using System.Collections.Generic;
using Serilog;
====
using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;
>>>> REPLACE

Use the *FULL* file path, as shown to you by the user.

Every *SEARCH* section must *EXACTLY MATCH* the existing file content, character for character, including all comments, docstrings, whitespace, etc.
If the file contains code or other data wrapped/escaped in json/xml/quotes or other containers, you need to propose edits to the literal contents of the file, including the container markup.

*SEARCH/REPLACE* blocks will replace the *FIRST* matching occurrence.
Include enough lines to make the SEARCH blocks uniquely match the lines to change.

Keep *SEARCH/REPLACE* blocks concise.
Break large *SEARCH/REPLACE* blocks into a series of smaller blocks that each change a small portion of the file.

To move code within a file, use 2 *SEARCH/REPLACE* blocks: 1 to delete it from its current location, 1 to insert it in the new location.

If you want to put code in a new file, use a *SEARCH/REPLACE block* with:
- A new file path, including dir name if needed
- An empty `SEARCH` section
- The new file's contents in the `REPLACE` section

If you want to delete a file, use a *SEARCH/REPLACE block* with:
- The file path
- An empty `SEARCH` section
- An empty `REPLACE` section


ONLY EVER RETURN CODE IN A *SEARCH/REPLACE BLOCK*!
"""


# class to represent a file operation (not used in any prompts)
class FileOperation(BaseModel):
    file_name: str
    search_block: str
    replace_block: str


class OperationApplier:
    def __init__(self, source_project: CodeProject, generation: str):
        self.source_project = source_project
        # convert the generation to a list of file operations
        # parse all file operations from the generation
        self.file_operations: list[FileOperation] = []
        self.all_success = True
        gen_lines = generation.split("\n")
        valid_path_pattern = re.compile(r"^[\w\-./\\]+$")

        for i, line in enumerate(gen_lines):
            if line.startswith("<<<< SEARCH"):
                # get the file name
                file_name = gen_lines[i - 1]
                if not file_name:
                    logging.warning(f"Empty file name: {file_name}")
                    self.all_success = False
                    continue
                if file_name[0] == '"' or file_name[0] == "'" or file_name[0] == "`":
                    file_name = file_name[1:]
                if file_name[-1] == '"' or file_name[-1] == "'" or file_name[-1] == "`":
                    file_name = file_name[:-1]

                file_name = os.path.normpath(file_name)
                # HACK: if the llm included the project name in the file path, remove it
                if file_name.startswith(source_project.display_name + "/"):
                    file_name = file_name[len(source_project.display_name) + 1 :]

                # check if it is a valid file path
                if not valid_path_pattern.match(file_name):
                    logging.warning(f"Invalid file name: {file_name}")
                    self.all_success = False
                    continue

                # get the search block
                search_block = ""
                valid_block = False
                for j in range(i + 1, len(gen_lines)):
                    if gen_lines[j] == "<<<< SEARCH" or gen_lines[j] == ">>>> REPLACE":
                        search_block += gen_lines[j] + "\n"
                        valid_block = False
                        break
                    if gen_lines[j] == "====":
                        valid_block = True
                        break
                    search_block += gen_lines[j] + "\n"
                if not valid_block:
                    logging.warning(
                        f"Invalid search block for file {file_name}:\n{search_block}"
                    )
                    self.all_success = False
                    continue
                # get the replace block
                replace_block = ""
                valid_block = False
                for j in range(j + 1, len(gen_lines)):
                    if gen_lines[j] == "====" or gen_lines[j] == "<<<< SEARCH":
                        replace_block += gen_lines[j] + "\n"
                        valid_block = False
                        break
                    if gen_lines[j] == ">>>> REPLACE":
                        valid_block = True
                        break
                    replace_block += gen_lines[j] + "\n"
                if not valid_block:
                    logging.warning(
                        f"Invalid replace block for file {file_name}:\n{replace_block}"
                    )
                    self.all_success = False
                    continue

                self.file_operations.append(
                    FileOperation(
                        file_name=file_name,
                        search_block=search_block,
                        replace_block=replace_block,
                    )
                )

    def apply(self) -> tuple[CodeProject, bool]:
        # Create a deep copy of the source project
        target_project: CodeProject = copy.deepcopy(self.source_project)

        logging.info(f"Applying {len(self.file_operations)} file operations")
        for file_operation in self.file_operations:
            # do not allow absolute paths
            if file_operation.file_name.startswith("/"):
                self.all_success = False
                logging.warning(
                    f"Absolute paths are not allowed: {file_operation.file_name}"
                )
                continue
            # do not allow paths with ".."
            if "../" in file_operation.file_name:
                self.all_success = False
                logging.warning(
                    f"Paths with '..' are not allowed: {file_operation.file_name}"
                )
                continue

            if file_operation.search_block == "" and file_operation.replace_block == "":
                success = target_project.remove_file(file_operation.file_name)
                if not success:
                    self.all_success = False
                    continue
                logging.info(f"Deleted file {file_operation.file_name}")
                continue

            if file_operation.search_block == "":
                # add the file to the target project
                target_project.add_file(
                    file_operation.file_name, file_operation.replace_block
                )
                logging.info(f"Created file {file_operation.file_name}")
                continue

            source_file = target_project.get_file(file_operation.file_name)
            if source_file is None:
                self.all_success = False
                logging.warning(f"No source file found for {file_operation.file_name}")
                continue

            # remove file encoding characters at the beginning of the file
            source_code = source_file.source_code
            removed_encoding = ""
            if source_code.startswith("\ufeff"):
                source_code = source_code[1:]
                removed_encoding = "\ufeff"
            if file_operation.search_block.startswith("\ufeff"):
                file_operation.search_block = file_operation.search_block[1:]
            if file_operation.replace_block.startswith("\ufeff"):
                file_operation.replace_block = file_operation.replace_block[1:]

            new_code = self.replace_code_block(
                source_code, file_operation.search_block, file_operation.replace_block
            )

            if new_code is None:
                self.all_success = False
                logging.warning(
                    f"Failed to update file {file_operation.file_name} with \n\nsearch block:\n\n{file_operation.search_block}\n\nreplace block:\n\n{file_operation.replace_block}"
                )
                continue

            if removed_encoding:
                new_code = removed_encoding + new_code

            source_file.source_code = new_code
            logging.info(
                f"Updated file {file_operation.file_name} with \nsearch block:\n{file_operation.search_block}\n\nreplace block:\n{file_operation.replace_block}"
            )

        # add debug information to the target project
        # target_project = self.save_debug_info(target_project)

        return target_project, self.all_success

    def replace_code_block(self, code_file_content, search_block, replace_block):
        if search_block in code_file_content:
            return code_file_content.replace(search_block, replace_block, 1)

        # Dedent and strip the search and replace blocks
        search_block_dedented = dedent(search_block).strip()
        replace_block_dedented = dedent(replace_block).strip()

        # Split the search block into lines
        search_lines = search_block_dedented.splitlines()

        # Escape each line and build the regex pattern
        escaped_lines = [re.escape(line.lstrip()) for line in search_lines]
        pattern = r"(?m)^\s*" + r"\s*\n^\s*".join(escaped_lines)

        # Define a function to adjust the indentation of the replace block
        def adjust_replace_block(match):
            # Get the indentation of the first line of the matched block
            first_line = match.group(0).splitlines()[0]
            indent = re.match(r"^\s*", first_line).group(0)
            # Adjust the replace block's indentation
            replace_lines = replace_block_dedented.splitlines()
            adjusted_replace = "\n".join(
                indent + line if line.strip() else line for line in replace_lines
            )
            return adjusted_replace

        # Use re.sub to perform the replacement
        new_code_file_content = re.sub(
            pattern, adjust_replace_block, code_file_content, count=1
        )
        return new_code_file_content

    def save_debug_info(self, target_project: CodeProject):
        # use difflib to make a text file with all the changes
        diff_file = ""
        n_changes = 0
        n_changed_files = 0
        for file in target_project.files:
            old_file = self.source_project.get_file(file.file_name)
            if old_file is None:
                # new file add all lines
                diff = [f"+ {line}" for line in file.source_code.split("\n")]
            else:
                diff = difflib.unified_diff(
                    old_file.source_code.split("\n"),
                    file.source_code.split("\n"),
                    lineterm="",
                )

                # continue if there is no diff
                diff = list(diff)
                if not diff:
                    continue

            n_changes += len(diff)
            n_changed_files += 1
            diff_file += f"Filename: {file.file_name}\n"
            diff_file += "\n".join(diff) + "\n\n"
            diff_file += "-" * 80 + "\n"

        diff_file = (
            f"Total changes: {n_changes}\nTotal changed files: {n_changed_files}\n\n"
            + diff_file
        )

        # save it in the target project
        target_project.add_file("diff.txt", diff_file)

        # save the operations as a text file in the target project
        op_file = ""
        for file_operation in self.file_operations:
            op_file += f"Filename: {file_operation.file_name}\n"
            op_file += f"Search block:\n{file_operation.search_block}\n"
            op_file += f"Replace block:\n{file_operation.replace_block}\n\n"
            op_file += "-" * 80 + "\n"
        target_project.add_file("operations.txt", op_file)
        return target_project
