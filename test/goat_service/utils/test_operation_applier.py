from textwrap import dedent

import pytest
from gs_common.CodeProject import CodeFile, CodeProject

from dataset.util import load_example_project
from src.goat_service.utils.operation_applier import FileOperation, OperationApplier


def test_apply_success():
    source = """\
namespace AdapterPattern
{
    internal static class Program
    {
    }
}
    """

    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Program.cs
<<<< SEARCH
    internal static class Program
    {
====
    internal static class TESTING
    {
>>>> REPLACE
    """

    gt = """\
namespace AdapterPattern
{
    internal static class TESTING
    {
    }
}
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("Program.cs").source_code == gt
    assert success


def test_apply_success_replace_first():
    source = """\
namespace AdapterPattern
{
    internal static class Program
    {
    }
    internal static class Program
    {
    }
}
    """

    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Program.cs
<<<< SEARCH
    internal static class Program
    {
====
    internal static class TESTING
    {
>>>> REPLACE
    """

    gt = """\
namespace AdapterPattern
{
    internal static class TESTING
    {
    }
    internal static class Program
    {
    }
}
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("Program.cs").source_code == gt
    assert success


def test_apply_create_file():
    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code="",
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
log4net.config
<<<< SEARCH
====
<?xml version="1.0" encoding="utf-8" ?>
<log4net>
>>>> REPLACE
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert len(result.files) == 2
    assert (
        result.get_file("log4net.config").source_code
        == """\
<?xml version="1.0" encoding="utf-8" ?>
<log4net>
"""
    )
    assert success


def test_apply_delete_file():
    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code="",
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Program.cs
<<<< SEARCH
====
>>>> REPLACE
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert len(result.files) == 0
    assert success


def test_apply_first_line_has_fileencoding_characters():
    source = "\ufeffnamespace AdapterPattern\n{\n    internal static class Program\n"
    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Program.cs
<<<< SEARCH
namespace AdapterPattern
====
namespace TESTING
>>>> REPLACE
    """
    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert (
        result.get_file("Program.cs").source_code
        == "\ufeffnamespace TESTING\n{\n    internal static class Program\n"
    )
    assert success


def test_apply_wrong_whitespace():
    source = """\
namespace AdapterPattern
{
    internal static class Program
    {
    }
}
    """

    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Program.cs
<<<< SEARCH
internal static class Program
{
====
internal static class TESTING
{
>>>> REPLACE
    """

    gt = """\
namespace AdapterPattern
{
    internal static class TESTING
    {
    }
}
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("Program.cs").source_code == gt
    assert success


def test_invalid_file_path():
    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code="",
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
new file path: log4net.config
<<<< SEARCH
====
<?xml version="1.0" encoding="utf-8" ?>
<log4net>
>>>> REPLACE
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert len(result.files) == 1
    assert not success


def test_apply_csproj_with_double_dot_filename():
    source = """\
  </ItemGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.CSharp" Version="4.7.0" />
  </ItemGroup>
  <Target Name="AfterBuild">
    """

    source_project = CodeProject(
        display_name="Hashids.Net",
        files=[
            CodeFile(
                file_name="Hashids.net.csproj",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Hashids.net.csproj
<<<< SEARCH
  <ItemGroup>
    <PackageReference Include="Microsoft.CSharp" Version="4.7.0" />
  </ItemGroup>
====
  <ItemGroup>
    <PackageReference Include="Microsoft.CSharp" Version="4.7.0" />
    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
  </ItemGroup>
>>>> REPLACE
    """

    gt = """\
  </ItemGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.CSharp" Version="4.7.0" />
    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
  </ItemGroup>
  <Target Name="AfterBuild">
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("Hashids.net.csproj").source_code == gt
    assert success


def test_apply_csproj_wrong_whitespace():
    source = """\
  </ItemGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.CSharp" Version="4.7.0" />
  </ItemGroup>
  <Target Name="AfterBuild">
    """

    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="AdapterPattern.csproj",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
AdapterPattern.csproj
<<<< SEARCH
<ItemGroup>
    <PackageReference Include="Microsoft.CSharp" Version="4.7.0" />
</ItemGroup>
====
<ItemGroup>
    <PackageReference Include="Microsoft.CSharp" Version="4.7.0" />
    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
</ItemGroup>
>>>> REPLACE
    """

    gt = """\
  </ItemGroup>
  <ItemGroup>
      <PackageReference Include="Microsoft.CSharp" Version="4.7.0" />
      <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
  </ItemGroup>
  <Target Name="AfterBuild">
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("AdapterPattern.csproj").source_code == gt
    assert success


def test_apply_invalid_block():
    source = """\
namespace AdapterPattern
{
    internal static class Program
    {
    }
}
    """

    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Program.cs
<<<< SEARCH
    internal static class Program
    {
====
    internal static class TESTING
    {
>>> REPLACE
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("Program.cs").source_code == source
    assert not success


def test_apply_one_valid_one_invalid_block():
    source = """\
namespace AdapterPattern
{
    internal static class Program
    {
    }
}
    """

    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Program.cs
<<<< SEARCH
    internal static class Program
    {
====
    internal static class TESTING
    {
>>> REPLACE

## next step 
Program.cs
<<<< SEARCH
    internal static class Program
    {
====
    internal static class TESTING
    {
>>>> REPLACE

    """

    gt = """\
namespace AdapterPattern
{
    internal static class TESTING
    {
    }
}
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("Program.cs").source_code == gt
    assert not success


def test_apply_indent2():
    source = """\
        private Regex guardsRegex;
        private Regex sepsRegex;
        private static Regex hexValidator = new Regex("^[0-9a-fA-F]+$", RegexOptions.Compiled);
        private static Regex hexSplitter = new Regex(@"[\w\W]{1,12}", RegexOptions.Compiled);

        public Hashids() : this(string.Empty, 0, DEFAULT_ALPHABET, DEFAULT_SEPS)
        { }

        public Hashids(string salt = "", int minHashLength = 0, string alphabet = DEFAULT_ALPHABET, string seps = DEFAULT_SEPS)
        {
            Logger.Information("Initializing Hashids with salt: {Salt}, minHashLength: {MinHashLength}, alphabet: {Alphabet}, seps: {Seps}", salt, minHashLength, alphabet, seps);

    """
    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Hashids.cs",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Hashids.cs
<<<< SEARCH
        public Hashids() : this(string.Empty, 0, DEFAULT_ALPHABET, DEFAULT_SEPS)
====
        static Hashids()
        {
            LoggerConfig.Configure();
        }

        public Hashids() : this(string.Empty, 0, DEFAULT_ALPHABET, DEFAULT_SEPS)
>>>> REPLACE
    """

    gt = """\
        private Regex guardsRegex;
        private Regex sepsRegex;
        private static Regex hexValidator = new Regex("^[0-9a-fA-F]+$", RegexOptions.Compiled);
        private static Regex hexSplitter = new Regex(@"[\w\W]{1,12}", RegexOptions.Compiled);

        static Hashids()
        {
            LoggerConfig.Configure();
        }

        public Hashids() : this(string.Empty, 0, DEFAULT_ALPHABET, DEFAULT_SEPS)
        { }

        public Hashids(string salt = "", int minHashLength = 0, string alphabet = DEFAULT_ALPHABET, string seps = DEFAULT_SEPS)
        {
            Logger.Information("Initializing Hashids with salt: {Salt}, minHashLength: {MinHashLength}, alphabet: {Alphabet}, seps: {Seps}", salt, minHashLength, alphabet, seps);

    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("Hashids.cs").source_code == gt
    assert success


def test_apply_source_and_generation_with_fileencoding_characters():
    source = """\
﻿namespace AdapterPattern
{
    internal static class Program
    {
    }
}
    """

    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="Program.cs",
                source_code=source,
            )
        ],
        source_language="dotnet8",
    )
    generation = """\
Program.cs
<<<< SEARCH
﻿namespace AdapterPattern
{
====
﻿using Serilog;

namespace AdapterPattern
{
>>>> REPLACE
    """

    gt = """\
﻿using Serilog;

namespace AdapterPattern
{
    internal static class Program
    {
    }
}
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert result.get_file("Program.cs").source_code == gt
    assert success


def test_init_invalid_name():
    invalid_file_name = (
        "LumenWorks.Framework.IO-GSTests/Csv/CachedCsvReader.CsvBindingListTests.cs"
    )
    source_project = CodeProject(
        display_name="AdapterPattern",
        files=[
            CodeFile(
                file_name="LumenWorks.Framework.IO-GSTests/Csv/CachedCsvReader.CsvBindingListTests.cs",
                source_code="",
            )
        ],
        source_language="dotnet8",
    )
    generation = f"""\
{invalid_file_name}
<<<< SEARCH
====
asdkljasdöklasjdkl
>>>> REPLACE
    """

    applier = OperationApplier(source_project, generation)
    result, success = applier.apply()

    assert success
    assert result.get_file(invalid_file_name).source_code == "asdkljasdöklasjdkl\n"
