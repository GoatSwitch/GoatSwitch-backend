import logging
import os
import subprocess

from gs_common.CodeProject import CodeProject


class UpgradeAssistant:
    def __init__(self, source_project: CodeProject, save_dir: str):
        self.source_project = source_project
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.source_project.save_to_dir(self.save_dir)

    def upgrade(self) -> CodeProject:
        # use cli upgrade assistant tool via subprocess
        # search files of source_project to find csproj file name
        csproj_files = [
            file
            for file in self.source_project.files
            if file.file_name.endswith(".csproj")
        ]
        if len(csproj_files) > 1:
            raise Exception("More than one csproj file found in source_project.files")
        if len(csproj_files) == 0:
            raise Exception("No csproj file found in source_project.files")
        path_to_csproj = csproj_files[0].file_name
        # NOTE: we need to be in the directory of the csproj file
        # else UA does not find Properties/AssemblyInfo.cs
        csproj_name = os.path.basename(path_to_csproj)
        path_to_csproj_dir = os.path.join(
            self.save_dir, os.path.dirname(path_to_csproj)
        )
        logging.info(f"csproj_name: {csproj_name}")
        logging.info(f"path_to_csproj_dir: {path_to_csproj_dir}")
        logging.info(f"raw csproj: {csproj_files[0].source_code}")

        # check if System.Drawing is in csproj[0]
        need_system_drawing_common = False
        if "System.Drawing" in csproj_files[0].source_code:
            need_system_drawing_common = True
        if "OrderTrackingDashboard" in self.source_project.display_name:
            need_system_drawing_common = False

        # run upgrade-assistant
        # TODO: gpt should be able to set targetFramework
        command = [
            "upgrade-assistant",
            "upgrade",
            "--non-interactive",
            "--targetFramework",
            "net8.0",
            "--operation",
            "Inplace",
            csproj_name,
        ]
        result = subprocess.run(
            command, cwd=path_to_csproj_dir, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            msg = f"Upgrade Assistant Error:\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            logging.error(msg)
            raise Exception(msg)

        # add system.drawing.common if needed
        if need_system_drawing_common:
            # use cli dotnet add package System.Drawing.Common
            command = [
                "dotnet",
                "add",
                csproj_name,
                "package",
                "System.Drawing.Common",
            ]
            result = subprocess.run(
                command,
                cwd=path_to_csproj_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                msg = f"Error adding System.Drawing.Common:\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
                logging.error(msg)
                raise Exception(msg)

        # load upgraded project
        upgraded_project = CodeProject.load_from_dir(
            display_name=self.source_project.display_name,
            base_dir=self.save_dir,
            source_language="dotnet8",
        )
        # split reference files
        upgraded_project.split_reference_files(
            relative_path_to_main_csproj=path_to_csproj
        )
        # remove reference files
        upgraded_project.reference_files = []

        # check if csproj is actually in new SDK format
        # for e.g. WindowsForms projects, UA does not convert the csproj
        csproj = next(
            file
            for file in upgraded_project.files
            if file.file_name.endswith(".csproj")
        )
        if '<Project Sdk="Microsoft.NET.Sdk' not in csproj.source_code:
            msg = f"Error: .csproj file is not in new SDK format. Output of UA:\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            logging.error(msg)
            raise Exception(msg)

        # HACK: manually replace UnsafeDeserialize to System.Text.Json.JsonSerializer.Deserialize
        replace_file_name = "Hashids.cs"
        replace_old1 = "using System.Runtime.Serialization.Formatters.Binary;"
        replace_new1 = "using System.Text.Json;"
        replace_old2 = "var formatter = new BinaryFormatter();"
        replace_new2 = ""
        replace_old3 = (
            "return (Hashids)formatter.UnsafeDeserialize(memoryStream, null);"
        )
        replace_new3 = "return JsonSerializer.Deserialize<Hashids>(new StreamReader(memoryStream).ReadToEnd());"
        for file in upgraded_project.files:
            if file.file_name == replace_file_name:
                file.source_code = file.source_code.replace(replace_old1, replace_new1)
                file.source_code = file.source_code.replace(replace_old2, replace_new2)
                file.source_code = file.source_code.replace(replace_old3, replace_new3)

        return upgraded_project
