# Workarounds

## Upgrade Assistant endpoint is blocking

- Bad because:
  - blocking calls for a kubernetes pod are not a best practice
  - probably better to set maxconcurrency in k8s
- Why the workaround?
  - UA is not meant to run in parallel (uses temp files; stuff gets overwritten)
  - When testing in parallel, this is a common issue

## Windows line endings are handled in gateway

- Bad because:
  - gateway is not supposed to do logic
- Why the workaround?
  - before, each python service had to handle the line endings separately
  - was leading to bugs

## Backup process is not awaited

- Bad because:
  - fire and forget is not a good practice, can lead to data loss
  - also if backup takes a long time and has a bug, it will be hard to find
- Why the workaround?
  - not sure how to handle it

## .NET test csproj is hardcoded

- Bad because:
  - not very flexible
  - e.g. sdk = normal sdk, not windowsdesktop
    - This might not be an issue since WPF and WinForms still function correctly.
    - The WindowsDesktop SDK primarily includes some additional namespaces automatically: [Implicit Using Directives](https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview#implicit-using-directives)
  - but there could be other issues
- Why the workaround?
  - we need control over the csproj file (e.g. setting the target framework, referencing other projects, etc.)
  - this could be more difficult to do with a generated csproj file
