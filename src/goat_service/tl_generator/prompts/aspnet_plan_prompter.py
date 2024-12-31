from src.goat_service.tl_generator.prompts.universal_plan_prompter import (
    UniversalPlanPrompter,
)

BUILT_IN_OPERATIONS = [
    "UPGRADE_DOTNET_PROJECT",
    "RESTRUCTURE_PROJECT_FROM_ASPNET_TO_ASPNETCORE",
]


ADDITIONAL_INFO = """
When modernizing a ASP.NET framework project to ASP.NET Core, do the following:
1. Upgrade the project from .NET Framework to .NET 8.0.
2. Create a Program.cs file for ASP.NET CORE .NET 8. Do not include auth, db or static files.
3. Restructure the project from ASP.NET to ASP.NET Core (Use RESTRUCTURE_PROJECT_FROM_ASPNET_TO_ASPNETCORE).
4. Refactor the csproj file for ASP.NET Core.
5. Refactor the cshtml files to use CDN files. 
    Use: cdn.jsdelivr.net for Bootstrap, jQuery.
    Use: cdnjs.cloudflare.com for Modernizr.
6. Generate appsettings.json file.
7. Generate launchsettings.json file with default port 6060.
Only do these steps for ASP.NET projects, not for normal .NET projects.

You can use built-in operations or create your own operations.
List of built-in operations:
{built_in_ops}
""".format(built_in_ops="\n".join(f"- {op}" for op in BUILT_IN_OPERATIONS))


class AspNetPlanPrompter(UniversalPlanPrompter):
    def get_additional_info(self) -> str:
        return ADDITIONAL_INFO
