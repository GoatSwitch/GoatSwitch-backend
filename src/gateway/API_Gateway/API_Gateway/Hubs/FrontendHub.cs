using System.Collections.Concurrent;
using System.Diagnostics;
using API_Gateway.Models.Project;
using API_Gateway.Models.TLGenerator;
using API_Gateway.Models.TLPicker;
using API_Gateway.Models.UTGenerator;
using API_Gateway.Models.UTPicker;
using API_Gateway.Models.Workflow;
using API_Gateway.Services;
using API_Gateway.Services.Exceptions;
using Microsoft.AspNetCore.SignalR;
using OpenTelemetry.Trace;
using Serilog.Context;

namespace API_Gateway.Hubs;

public class FrontendHub : Hub
{
    private readonly ILogger<FrontendHub> _logger;
    private readonly IUTPickerCallerService _utPickerCallerService;
    private readonly IUTGeneratorCallerService _utGeneratorCallerService;
    private readonly ITLGeneratorCallerService _tlGeneratorCallerService;
    private readonly IPlanGeneratorCallerService _planGeneratorCallerService;
    private readonly ITLPickerCallerService _tlPickerCallerService;
    private readonly ConcurrentBag<Task> _tasks = [];
    private readonly IAuthorizedUserService _authorizedUserService;
    private readonly IBackupService _backupService;

    public FrontendHub(
        ILogger<FrontendHub> logger,
        IUTPickerCallerService utPickerCallerService,
        IUTGeneratorCallerService utGeneratorCallerService,
        ITLGeneratorCallerService tlGeneratorCallerService,
        IPlanGeneratorCallerService planGeneratorCallerService,
        ITLPickerCallerService tlPickerCallerService,
        IAuthorizedUserService authorizedUserService,
        IBackupService backupService
    )
    {
        this._logger = logger;
        this._utPickerCallerService = utPickerCallerService;
        this._utGeneratorCallerService = utGeneratorCallerService;
        this._tlGeneratorCallerService = tlGeneratorCallerService;
        this._planGeneratorCallerService = planGeneratorCallerService;
        this._tlPickerCallerService = tlPickerCallerService;
        this._authorizedUserService = authorizedUserService;
        this._backupService = backupService;
        this.SubscribeAllEvents(this._utGeneratorCallerService.SignalRLogService);
        this.SubscribeAllEvents(this._tlGeneratorCallerService.SignalRLogService);
        this.SubscribeAllEvents(this._planGeneratorCallerService.SignalRLogService);
        this.SubscribeAllEvents(this._utPickerCallerService.SignalRLogService);
        this.SubscribeAllEvents(this._tlPickerCallerService.SignalRLogService);
    }

    private void SubscribeAllEvents(ISignalRLogService service)
    {
        service.SendProgressUpdateEvent += (a, b) => this._tasks.Add(this.SendProgressUpdateAsync(a, b));
        service.SendToLogViewEvent += (a, b) => this._tasks.Add(this.SendToLogViewAsync(a, b));
        service.SendUTCandidatesEvent += (a, b) => this._tasks.Add(this.SendUTCandidatesAsync(a, b));
        service.SendUTResultEvent += (a, b) => this._tasks.Add(this.SendUTResultAsync(a, b));
        service.SendTranslationCandidatesEvent += (a, b) => this._tasks.Add(this.SendTranslationCandidatesAsync(a, b));
        service.SendTranslationResultEvent += (a, b) => this._tasks.Add(this.SendTranslationResultAsync(a, b));
        service.SendAssessmentResultEvent += (a, b) => this._tasks.Add(this.SendAssessmentResultAsync(a, b));
    }

    public override async Task OnConnectedAsync()
    {
        var httpContext = Context.GetHttpContext();
        if (httpContext == null)
        {
            this._logger.LogError("HttpContext is null");
            return;
        }
        var accessToken = httpContext.Request.Query["access_token"].ToString() ?? "";
        bool isAuth;
        try
        {
            isAuth = await this._authorizedUserService.IsAuthorized(accessToken);
        }
        catch (Exception e)
        {
            this._logger.LogError(e, "Error occurred while checking if user is authorized");
            isAuth = false;
        }
        if (isAuth)
        {
            this.Context.Items["CompanyID"] = this._authorizedUserService.CompanyID;
            this.Context.Items["UserID"] = this._authorizedUserService.UserID;
            LogContext.PushProperty("UserID", this._authorizedUserService.UserID);
            LogContext.PushProperty("CompanyID", this._authorizedUserService.CompanyID);
            this._logger.LogInformation("User successfully authorized");
        }
        else
        {
            // If the user is not authorized, disconnect
            string errorMessage = "You are not authorized to use this service.";
            this._logger.LogError($"User with token {accessToken} is not authorized");
            await this.Clients.Client(this.Context.ConnectionId).SendAsync("logTerminal", errorMessage, "error");
            // close the connection
            await this.OnDisconnectedAsync(new Exception(errorMessage));
            this.Context.Abort();
            return;
        }
        await base.OnConnectedAsync();
    }

    public async Task WorkflowWrapper(ActivitySource act_source, Func<Task> action)
    {
        // Create a new root activity
        Activity.Current = null;
        this._logger.LogInformation($"Starting workflow: {act_source.Name}");
        Activity activity =
            act_source.StartActivity(act_source.Name)
            ?? throw new Exception(
                @"Failed to start activity,
                                        are you sure the activity source is correct?"
            );
        string connectionId = this.Context.ConnectionId;
        string userID = this.Context.Items["UserID"]?.ToString() ?? "unknown";
        if (userID != AuthorizedUserService.DefaultUserID)
        {
            // set user id to connection id if it is not set
            userID = connectionId;
        }
        string companyID = this.Context.Items["CompanyID"]?.ToString() ?? "unknown";
        activity.SetBaggage("UserID", userID);
        activity.SetBaggage("CompanyID", companyID);
        activity.AddTag("UserID", userID)
            .AddTag("CompanyID", companyID);
        activity.AddEvent(new ActivityEvent("Workflow started"));

        string traceId = activity.TraceId.ToString();

        using (LogContext.PushProperty("TraceID", traceId))
        using (LogContext.PushProperty("UserID", userID))
        using (LogContext.PushProperty("CompanyID", companyID))
        {
            this._logger.LogInformation($"Connection ID: {connectionId}");
            this._logger.LogInformation($"Span ID: {activity.SpanId}");
            this._logger.LogInformation($"Parent ID: {activity.ParentSpanId}");
            await this.SendToLogViewAsync($"Trace ID: {traceId}");
            try
            {
                await this.SendProgressUpdateAsync(WSteps.KEY_STEP1, WStates.STATE_PENDING);
                await this.SendProgressUpdateAsync(WSteps.KEY_STEP2, WStates.STATE_PENDING);
                await this.SendProgressUpdateAsync(WSteps.KEY_STEP3, WStates.STATE_PENDING);

                await action();
                activity.SetStatus(Status.Ok);
            }
            catch (GSBaseException e)
            {
                // GSExceptions are already logged to user; no need for SendToLogViewAsync
                activity.SetStatus(Status.Error);
                this._logger.LogError(e, "Unexpected GSBaseException occurred");
            }
            catch (Exception e)
            {
                this._logger.LogError(e, "Unexpected error occurred");
                var exception = new GSBaseException(e.Message);
                await this.SendToLogViewAsync(exception.UserMessage, "error");
                activity.SetStatus(Status.Error);
            }
            try
            {
                await Task.WhenAll(this._tasks);
            }
            catch (GSBaseException e)
            {
                // GSExceptions are already logged to user; no need for SendToLogViewAsync
                activity.SetStatus(Status.Error);
                this._logger.LogError(e, "GSBaseException occurred while waiting for tasks to complete in the bag");
            }
            catch (Exception e)
            {
                this._logger.LogError(e, "Error occurred while waiting for tasks to complete in the bag");
                var exception = new GSBaseException(e.Message);
                await this.SendToLogViewAsync(exception.UserMessage, "error");
                activity.SetStatus(Status.Error);
            }
        }
        activity.AddEvent(new ActivityEvent("Workflow completed"));
        activity.Stop();
    }

    public async Task WorkflowBasicAsync(CodeProject sourceProject, string targetLanguage)
    /*
    * generate tests -> pick tests -> generate translations -> pick translation
    */
    {
        string model = "default";
        if (sourceProject.SourceLanguage == "dotnetframework" && targetLanguage == "dotnet8")
        {
            model = "UPGRADE_DOTNET_PROJECT";
        }
        ActivitySource act_source = new("WorkflowMigrate");
        await WorkflowWrapper(
            act_source,
            async () =>
            {
                string traceId = Activity.Current?.TraceId.ToString() ?? "traceid-missing";
                this._logger.LogInformation(
                    $"Started: Migrate {sourceProject.DisplayName} from {sourceProject.SourceLanguage} to {targetLanguage}"
                );
                _ = _backupService.Backup(sourceProject, traceId, act_source.Name, "sourceProject");
                if (model == "UPGRADE_DOTNET_PROJECT")
                {
                    // // start Assessment via TLGenerator
                    // Task<TLGeneratorResponse> assessTask = this._tlGeneratorCallerService.AssessAsync(
                    //     sourceProject,
                    //     targetLanguage
                    // );
                    // this._tasks.Add(assessTask);
                }

                // Translation and UT generation run in parallel
                Task<TLGeneratorResponse> genTLTask = this._tlGeneratorCallerService.GenerateTLAsync(
                    sourceProject,
                    targetLanguage,
                    model
                );
                this._tasks.Add(genTLTask);
                Task<UTGeneratorResponse> genUTTask = this._utGeneratorCallerService.GenerateUTAsync(
                    sourceProject,
                    testProject: null,
                    targetLanguage: targetLanguage
                );
                UTGeneratorResponse utGenResponse = await genUTTask;
                Task<UTPickerResponse> pickUTTask = this._utPickerCallerService.PickUTAsync(
                    sourceProject,
                    utGenResponse.Solutions,
                    targetLanguage
                );

                // NOTE: The order of the responses is important
                // await genTask first because genTLTask is in bag -> will be await anyway
                UTPickerResponse utPickerResponse = await pickUTTask;
                if (utPickerResponse.ReturnCode != Models.UTPicker.Proto.ReturnCode.Success)
                {
                    throw new UTPException("Picking unit tests failed");
                }
                TLGeneratorResponse tlGeneratorResponse = await genTLTask;
                TLPickerResponse res = await this._tlPickerCallerService.PickAsync(
                    sourceProject,
                    utPickerResponse.Solution,
                    tlGeneratorResponse.Solutions,
                    targetLanguage
                );
                if (res.ReturnCode != Models.TLPicker.Proto.ReturnCode.Success)
                {
                    throw new TLPException("Picking translation failed");
                }
            }
        );
    }

    public async Task<string> WorkflowGenPlanAsync(CodeProject sourceProject, string instruction)
    {
        // NOTE: would be nice to start with a user test project here; but we cannot parse user test projects yet
        ActivitySource act_source = new("WorkflowGenPlan");
        string targetLanguage = "gslite";
        string plan_result = "";
        if (instruction == "")
        {
            instruction = """
            Please modernize this project. 
            Depending on the project, you could do the following things:
            - Refactor magic numbers and strings
            - Refactor to use modern language features
            - Add docstrings to the most important functions
            - Fix most common deprecations for this language
            - Optimize loops and other performance-critical parts
            - Refactor large functions into smaller ones
            - Improve error handling

            Do not do all of the above, just pick a few things that you think are most important given the codebase.
            """;
        }
        await WorkflowWrapper(
            act_source,
            async () =>
            {
                string traceId = Activity.Current?.TraceId.ToString() ?? "traceid - missing";
                this._logger.LogInformation(
                    $"Started: GenPlan {sourceProject.DisplayName} {sourceProject.SourceLanguage}"
                );
                _ = _backupService.Backup(sourceProject, traceId, act_source.Name, "sourceProject");

                // send UT progress update completed for GSClient
                await this.SendProgressUpdateAsync(WSteps.KEY_STEP1, WStates.STATE_COMPLETED);

                if (sourceProject.DisplayName == "OrderTrackingDashboard")
                {
                    plan_result = """
                    # AI Plan
                    ## Step 1: UPGRADE_DOTNET_PROJECT
                    Upgrade the project from .NET Framework 4.8 to.NET 8.0.This includes updating the project file to use the new SDK style format and removing old Framework references.
                    ## Step 2: CREATE_PROGRAM_FILE
                    Create a new Program.cs file with minimal ASP.NET Core 8.0 setup without authentication, database or static files configuration.
                    ## Step 3: RESTRUCTURE_PROJECT_FROM_ASPNET_TO_ASPNETCORE
                    Restructure the project to follow ASP.NET Core conventions, including updating controller base classes, removing Web.config, and updating namespace references.
                    ## Step 4: UPDATE_CSPROJ
                    Update the project file to use the new ASP.NET Core references and needed packages for the application.
                    ## Step 5: UPDATE_LAYOUT_REFERENCES
                    Update _Layout.cshtml to use CDN references for Bootstrap (cdn.jsdelivr.net), jQuery (cdn.jsdelivr.net), and Modernizr (cdnjs.cloudflare.com). Remove old bundling references.
                    ## Step 6: CREATE_APPSETTINGS
                    Create appsettings.json file with basic configuration settings for the application.
                    ## Step 7: CREATE_LAUNCHSETTINGS
                    Create launchSettings.json file in the Properties folder with default port 6060 configuration.
                    ## Step 8: CLEANUP_OLD_FILES
                    Remove old ASP.NET Framework specific files like Global.asax, Web.config, packages.config, and App_Start folder contents.
                    """;

                    // send tl progress update completed
                    await this.SendProgressUpdateAsync(WSteps.KEY_STEP2, WStates.STATE_COMPLETED);
                }
                else
                {
                    PlanGeneratorResponse planGeneratorResponse = await this._planGeneratorCallerService.GeneratePlanAsync(
                        sourceProject,
                        targetLanguage: targetLanguage,
                        instruction: instruction
                    );
                    plan_result = planGeneratorResponse.Plan.ToString();
                }

                // send validate progress update completed
                await this.SendProgressUpdateAsync(WSteps.KEY_STEP3, WStates.STATE_COMPLETED);
            }
        );
        await this.SendReturnWorkflowGenPlanAsync(plan_result, "info");
        this._logger.LogInformation($"Plan generated: {plan_result}");
        return plan_result;
    }

    public async Task WorkflowExecutePlanAsync(CodeProject sourceProject, string instruction)
    {
        ActivitySource act_source = new("WorkflowExecutePlan");
        await WorkflowWrapper(
            act_source,
            async () =>
            {
                string traceId = Activity.Current?.TraceId.ToString() ?? "traceid-missing";
                this._logger.LogInformation($"Started: ExecutePlan {sourceProject.DisplayName} {sourceProject.SourceLanguage}");
                _ = _backupService.Backup(sourceProject, traceId, act_source.Name, "sourceProject");

                // enable ut validation if company != 1337
                bool validate = this._authorizedUserService.CompanyID != "1337";
                bool autofix = true;


                // Parse plan
                AIPlan plan = AIPlan.FromString(instruction);

                // Loop over plan, execute each step and send result of each step to frontend
                CodeProject? testProject = null;
                int step = 1;
                bool sentTranslationResult = false;
                bool shouldSendTestResult = false;
                List<int> failed_steps = [];
                foreach (Operation operation in plan.Operations)
                {
                    try
                    {
                        // make next prompt
                        string prompt = plan.ToString();
                        prompt += $"\n\n# Current task: {operation.OperationName}.\n{operation.Description}\n";
                        prompt += "Only complete the current task. Avoid working ahead.\n";

                        // determine operation
                        string model = operation.OperationName;
                        if (operation.OperationName == "GENERATE_TESTS")
                        {
                            shouldSendTestResult = true;
                            testProject = await this.ExecutePlanHandleGenTests(
                                sourceProject: sourceProject,
                                instruction: prompt,
                                targetLanguage: "gslite",
                                testProject: testProject,
                                validate: validate,
                                autofix: autofix
                            );
                        }
                        else
                        {
                            sourceProject = await this.ExecutePlanHandleGenTranslation(
                                sourceProject: sourceProject,
                                instruction: prompt,
                                targetLanguage: "gslite",
                                model: model
                            );
                            sentTranslationResult = true;
                        }

                        // backup after each step
                        _ = _backupService.Backup(sourceProject, traceId, act_source.Name, $"sourceProject_step{step}");
                        if (testProject != null && testProject.Files.Count > 0)
                        {
                            _ = _backupService.Backup(testProject, traceId, act_source.Name, $"testProject_step{step}");
                        }
                        await this.SendToLogViewAsync($"Step {step} completed", "info");
                        step += 1;
                    }
                    catch (Exception e)
                    {
                        // TODO: if timeout err try again once
                        this._logger.LogError(e, $"Error occurred during step {step}");
                        await this.SendToLogViewAsync($"Error occurred during step {step}", "error");
                        failed_steps.Add(step);
                        step += 1;
                    }
                }
                if (failed_steps.Count == 0)
                {
                    string msg = "All steps completed.";
                    await this.SendToLogViewAsync(msg, "info");
                    this._logger.LogInformation(msg);
                }
                else
                {
                    string msg = $"Workflow completed, but some steps failed: {string.Join(", ", failed_steps)}";
                    this._logger.LogError(msg);
                    await this.SendToLogViewAsync(msg, "error");
                }
                if (!sentTranslationResult)
                {
                    // NOTE: Frontend needs always at least one call to send the last translation result
                    //  otherwise it hangs for X minutes
                    // can happen if: no genTL steps in plan or no genTL step was without error
                    await this.SendTranslationResultAsync(
                        new TLPickerResponse(
                            solution: sourceProject,
                            testOutput: "",
                            error: "",
                            returnCode: Models.TLPicker.Proto.ReturnCode.Success
                        ),
                        "info"
                    );
                }
                if (shouldSendTestResult && testProject == null)
                {
                    // there was a genTests step, but no tests were generated
                    await this.SendProgressUpdateAsync(WSteps.KEY_STEP2, WStates.STATE_ERROR);
                }
                // send validate progress update completed
                await this.SendProgressUpdateAsync(WSteps.KEY_STEP3, WStates.STATE_COMPLETED);
            }
        );
    }

    private async Task<CodeProject> ExecutePlanHandleGenTranslation(
        CodeProject sourceProject,
        string instruction,
        string targetLanguage,
        string model
    )
    {
        TLGeneratorResponse tlGeneratorResponse = await this._tlGeneratorCallerService.GenerateTLAsync(
            sourceProject,
            targetLanguage: targetLanguage,
            model: model,
            instruction: instruction
        );

        // send current solution to frontend
        var returnCode = Models.TLPicker.Proto.ReturnCode.Success;
        if (tlGeneratorResponse.ReturnCode != Models.TLGenerator.Proto.ReturnCode.Success)
        {
            returnCode = Models.TLPicker.Proto.ReturnCode.Error;
        }
        await this.SendTranslationResultAsync(
            new TLPickerResponse(
                // return first
                tlGeneratorResponse.Solutions[0],
                tlGeneratorResponse.Error,
                returnCode: returnCode,
                testOutput: ""
            ),
            "info"
        );
        return tlGeneratorResponse.Solutions[0];
    }


    private async Task<CodeProject> ExecutePlanHandleGenTests(
        CodeProject sourceProject,
        string instruction,
        string targetLanguage,
        CodeProject? testProject,
        bool validate = false,
        bool autofix = true
    )
    {
        // gen tests
        UTGeneratorResponse utGenResponse = await this._utGeneratorCallerService.GenerateUTAsync(
            sourceProject,
            testProject: testProject,
            // targetLanguage: targetLanguage,
            targetLanguage: sourceProject.SourceLanguage,
            instruction: instruction
        );

        // handle error by continuing with next step
        if (utGenResponse.ReturnCode != Models.UTGenerator.Proto.ReturnCode.Success)
        {
            // return old test project, since new ones are not valid
            return testProject;
        }

        // if validate do not execute picker; just return first
        if (!validate)
        {
            // make a utpickerresponse
            // send utresult
            // this.SignalRLogService.SendUTResult(utPickerResponse);
            await this.SendUTResultAsync(
                new UTPickerResponse(
                    solution: utGenResponse.Solutions[0],
                    testOutput: "",
                    error: "",
                    returnCode: Models.UTPicker.Proto.ReturnCode.Success
                ),
                "info"
            );
            return utGenResponse.Solutions[0];
        }

        // pick tests with targetLanguage = sourceLanguage
        UTPickerResponse utPickerResponse = await this._utPickerCallerService.PickUTAsync(
            sourceProject,
            test_projects: utGenResponse.Solutions,
            targetLanguage: sourceProject.SourceLanguage
        );

        // if autofix is disabled, exit early
        if (autofix == false)
        {
            return utPickerResponse.Solution;
        }

        // handle error cases
        if (utPickerResponse.ReturnCode == Models.UTPicker.Proto.ReturnCode.FailedSourceCompile)
        {
            // NOTE: FailedSourceCompile is not used in backend right now
            this._logger.LogError("Source project does not compile, cannot autofix");
            // return first of newly generated test projects
            return utPickerResponse.Solution;
        }

        if (utPickerResponse.ReturnCode == Models.UTPicker.Proto.ReturnCode.FailedTestExecution || utPickerResponse.ReturnCode == Models.UTPicker.Proto.ReturnCode.FailedTestCompile)
        {
            // autofix tests
            this._logger.LogError("Tests have errors, trying to autofix");

            // update prompt
            if (!string.IsNullOrEmpty(utPickerResponse.TestOutput))
            {
                instruction = "Please fix this:\n" + utPickerResponse.TestOutput;
            }
            else
            {
                instruction = "Please fix this:\n" + utPickerResponse.Error;
            }

            // gen tests again
            utGenResponse = await this._utGeneratorCallerService.GenerateUTAsync(
                sourceProject,
                testProject: utPickerResponse.Solution,
                targetLanguage: targetLanguage,
                instruction: instruction
            );

            // pick tests with targetLanguage = sourceLanguage
            utPickerResponse = await this._utPickerCallerService.PickUTAsync(
                sourceProject,
                test_projects: utGenResponse.Solutions,
                targetLanguage: sourceProject.SourceLanguage
            );
        }
        return utPickerResponse.Solution;
    }

    public async Task WorkflowGenerateTestsAsync(CodeProject sourceProject, string instruction, CodeProject testProject)
    {
        ActivitySource act_source = new("WorkflowGenerateTests");
        await WorkflowWrapper(
            act_source,
            async () =>
            {
                // NOTE: in frontend generateTests is hardcoded to only work w csprojs
                string[] available_langs = ["dotnetframework", "dotnet8"];
                if (!available_langs.Contains(sourceProject.SourceLanguage))
                {
                    this._logger.LogInformation($"Generate tests for {sourceProject.DisplayName} (lang: {sourceProject.SourceLanguage}) is not supported; returning");
                    return;
                }
                string targetLanguage = "dotnet8";
                string traceId = Activity.Current?.TraceId.ToString() ?? "traceid-missing";
                this._logger.LogInformation($"Started: Generate tests for {sourceProject.DisplayName} andl lang: {sourceProject.SourceLanguage}");
                _ = _backupService.Backup(sourceProject, traceId, act_source.Name, "sourceProject");
                if (testProject != null && testProject.Files.Count > 0)
                {
                    _ = _backupService.Backup(testProject, traceId, act_source.Name, "testProject");
                }

                testProject = await this.ExecutePlanHandleGenTests(
                    sourceProject: sourceProject,
                    instruction: instruction,
                    targetLanguage: targetLanguage,
                    testProject: testProject,
                    validate: true,
                    autofix: true
                );

            }
        );
    }

    public async Task WorkflowGivenCandidatesAsync(
        CodeProject sourceProject,
        List<CodeProject> testCandidates,
        List<CodeProject> translationCandidates,
        string targetLanguage
    )
    {
        ActivitySource act_source = new("WorkflowRetry");
        await WorkflowWrapper(
            act_source,
            async () =>
            {
                // HACK: set language of translated project to target_language (later extension will do it)
                for (int i = 0; i < translationCandidates.Count; i++)
                {
                    translationCandidates[i].SourceLanguage = targetLanguage;
                }

                string traceId = Activity.Current?.TraceId.ToString() ?? "traceid-missing";
                this._logger.LogInformation(
                    $"Started: Retry {sourceProject.DisplayName} from {sourceProject.SourceLanguage} to {targetLanguage}"
                );
                _ = _backupService.Backup(sourceProject, traceId, act_source.Name, "sourceProject");
                _ = _backupService.Backup(testCandidates, traceId, act_source.Name, "testCandidates");
                _ = _backupService.Backup(translationCandidates, traceId, act_source.Name, "translationCandidates");

                UTPickerResponse utPickerResponse = await this._utPickerCallerService.PickUTAsync(
                    sourceProject,
                    testCandidates,
                    targetLanguage
                );
                if (utPickerResponse.ReturnCode != Models.UTPicker.Proto.ReturnCode.Success)
                {
                    throw new UTPException("Picking unit tests failed");
                }
                TLPickerResponse res = await this._tlPickerCallerService.PickAsync(
                    sourceProject,
                    utPickerResponse.Solution,
                    translationCandidates,
                    targetLanguage
                );
                if (res.ReturnCode != Models.TLPicker.Proto.ReturnCode.Success)
                {
                    throw new TLPException("Picking translation failed");
                }
            }
        );
    }

    public async Task WorkflowImproveTranslationAsync(
        CodeProject sourceProject,
        CodeProject testProject,
        CodeProject translatedProject,
        string instruction,
        string targetLanguage
    )
    {
        ActivitySource act_source = new("WorkflowImprove");
        await WorkflowWrapper(
            act_source,
            async () =>
            {
                // HACK: set language of translated project to target_language (later extension will do it)
                translatedProject.SourceLanguage = targetLanguage;

                string traceId = Activity.Current?.TraceId.ToString() ?? "traceid-missing";
                this._logger.LogInformation(
                $"Started: Improve {sourceProject.DisplayName} with {instruction}"
                );
                _ = _backupService.Backup(sourceProject, traceId, act_source.Name, "sourceProject");
                if (testProject != null && testProject.Files.Count > 0)
                {
                    _ = _backupService.Backup(testProject, traceId, act_source.Name, "testProject");
                }
                _ = _backupService.Backup(translatedProject, traceId, act_source.Name, "translationProject");

                // Start GenTL in the background
                Task<TLGeneratorResponse> genTLTask = this._tlGeneratorCallerService.GenerateTLAsync(
                    translatedProject,
                    targetLanguage,
                    instruction: instruction
                );
                this._tasks.Add(genTLTask);

                List<CodeProject> testProjects = [];
                if (testProject != null && testProject.Files.Count > 0)
                {
                    testProjects.Add(testProject);
                }
                else
                {
                    // if we don't have tests, generate them using the instruction as a hint
                    UTGeneratorResponse utGenResponse = await this._utGeneratorCallerService.GenerateUTAsync(
                        sourceProject,
                        testProject: null,
                        targetLanguage: targetLanguage,
                        instruction: instruction
                    );
                    testProjects = utGenResponse.Solutions;
                }

                Task<UTPickerResponse> pickUTTask = this._utPickerCallerService.PickUTAsync(
                    sourceProject,
                    testProjects,
                    targetLanguage
                );

                // NOTE: The order of the responses is important
                // await genTask first because genTLTask is in bag -> will be await anyway
                UTPickerResponse utPickerResponse = await pickUTTask;
                if (utPickerResponse.ReturnCode != Models.UTPicker.Proto.ReturnCode.Success)
                {
                    throw new UTPException("Picking unit tests failed");
                }
                TLGeneratorResponse tlGeneratorResponse = await genTLTask;

                // NOTE: for timprove, we give the current best tl_project as sourceProject to the TLPicker
                TLPickerResponse res = await this._tlPickerCallerService.PickAsync(
                    translatedProject,
                    utPickerResponse.Solution,
                    tlGeneratorResponse.Solutions,
                    targetLanguage
                );
                if (res.ReturnCode != Models.TLPicker.Proto.ReturnCode.Success)
                {
                    throw new TLPException("Picking translation failed");
                }
            }
        );
    }

    private async Task SendUTResultAsync(UTPickerResponse resp, string level = "info")
    {
        await this.Clients.Client(this.Context.ConnectionId).SendAsync("logUTResult", resp, level);
    }

    private async Task SendUTCandidatesAsync(List<CodeProject> testCandidates, string level = "info")
    {
        await this.Clients.Client(this.Context.ConnectionId).SendAsync("logUT", testCandidates, level);
    }

    private async Task SendTranslationCandidatesAsync(TLGeneratorResponse resp, string level = "info")
    {
        await this.Clients.Client(this.Context.ConnectionId).SendAsync("logTranslationCandidates", resp, level);
    }

    private async Task SendReturnWorkflowGenPlanAsync(string plan, string level = "info")
    {
        await this.Clients.Client(this.Context.ConnectionId).SendAsync("returnWorkflowGenPlanAsync", plan, level);
    }

    private async Task SendTranslationResultAsync(TLPickerResponse resp, string level = "info")
    {
        await this.Clients.Client(this.Context.ConnectionId).SendAsync("logTranslationResult", resp, level);
    }

    private async Task SendAssessmentResultAsync(TLGeneratorResponse resp, string level = "info")
    {
        await this.Clients.Client(this.Context.ConnectionId).SendAsync("logAssessmentResult", resp, level);
    }

    private async Task SendProgressUpdateAsync(string key, string progressState)
    {
        await this
            .Clients.Client(this.Context.ConnectionId)
            .SendAsync("updateProgress", new { key = key, progress_state = progressState });
    }

    private async Task SendToLogViewAsync(string message, string level = "info")
    {
        await this.Clients.Client(this.Context.ConnectionId).SendAsync("logLogs", message, level);
    }
}
