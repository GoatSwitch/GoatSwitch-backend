import pytest
from src.goat_service.tl_generator.prompts.universal_plan_prompter import (
    Operation,
    AIPlan,
)


def test_operation_plan_parse():
    plan = """\
# AI Plan
## Step 1: UPGRADE_DOTNET_PROJECT
Upgrade the project to .Net 8
## Step 2: INTEGRATE_LIBRARY
Integrate the library Serilog
In cs and csproj files.
"""
    parsed_plan = AIPlan.from_string(plan)
    assert len(parsed_plan.operations) == 2
    assert parsed_plan.operations[0].operation_name == "UPGRADE_DOTNET_PROJECT"
    assert parsed_plan.operations[1].operation_name == "INTEGRATE_LIBRARY"
    assert parsed_plan.operations[0].description == "Upgrade the project to .Net 8\n"
    assert (
        parsed_plan.operations[1].description
        == "Integrate the library Serilog\nIn cs and csproj files.\n"
    )


def test_operation_plan_str():
    plan = AIPlan(
        operations=[
            Operation(
                description="Upgrade the project to .Net 8\n",
                operation_name="UPGRADE_DOTNET_PROJECT",
            ),
            Operation(
                description="Integrate the library Serilog\nIn cs and csproj files.\n",
                operation_name="INTEGRATE_LIBRARY",
            ),
        ]
    )
    assert (
        str(plan)
        == """\
# AI Plan
## Step 1: UPGRADE_DOTNET_PROJECT
Upgrade the project to .Net 8

## Step 2: INTEGRATE_LIBRARY
Integrate the library Serilog
In cs and csproj files.

"""
    )


def test_parse_and_str():
    plan = """\
# AI Plan
## Step 1: UPGRADE_DOTNET_PROJECT
Upgrade the project to .Net 8

## Step 2: INTEGRATE_LIBRARY
Integrate the library Serilog
In cs and csproj files.

"""
    parsed_plan = AIPlan.from_string(plan)
    assert str(parsed_plan) == plan
    assert AIPlan.from_string(str(parsed_plan)) == parsed_plan


def test_str_and_parse():
    plan = AIPlan(
        operations=[
            Operation(
                description="Upgrade the project to .Net 8\n",
                operation_name="UPGRADE_DOTNET_PROJECT",
            ),
            Operation(
                description="Integrate the library Serilog\nIn cs and csproj files.\n",
                operation_name="INTEGRATE_LIBRARY",
            ),
        ]
    )
    assert AIPlan.from_string(str(plan)) == plan
    assert str(AIPlan.from_string(str(plan))) == str(plan)


def test_parse_error():
    # test no operations
    plan = """\
# AI Plan
"""
    with pytest.raises(ValueError):
        AIPlan.from_string(plan)

    # test no description (valid)
    plan = """\
# AI Plan
## Step 1: UPGRADE_DOTNET_PROJECT
"""
    AIPlan.from_string(plan)

    # test no operation
    plan = """\
# AI Plan
# Step 1: UPGRADE_DOTNET_PROJECT
Upgrade the project to .Net 8
# Step 2: INTEGRATE_LIBRARY
Integrate the library Serilog
"""
    with pytest.raises(ValueError):
        AIPlan.from_string(plan)


def test_str_error():
    # test no operations
    plan = AIPlan(operations=[])
    with pytest.raises(ValueError):
        str(plan)


def test_parse_ignore_other_lines():
    plan = """\
# AI Plan
## Step 1: UPGRADE_DOTNET_PROJECT
Upgrade the project to .Net 8
## Step 2: INTEGRATE_LIBRARY
Integrate the library Serilog

# Current task: UPGRADE_DOTNET_PROJECT
Upgrade the project to .Net 8
"""
    parsed_plan = AIPlan.from_string(plan)
    assert len(parsed_plan.operations) == 2
    assert parsed_plan.operations[0].operation_name == "UPGRADE_DOTNET_PROJECT"
    assert parsed_plan.operations[1].operation_name == "INTEGRATE_LIBRARY"
    assert parsed_plan.operations[0].description == "Upgrade the project to .Net 8\n"
    assert parsed_plan.operations[1].description == "Integrate the library Serilog\n"
