using API_Gateway.Models.Project;
using API_Gateway.Models.UTPicker;
using API_Gateway.Models.Workflow;
using API_Gateway.Services.Exceptions;
using Dapr.Client;
using GSProtoUT = API_Gateway.Models.UTPicker.Proto;

namespace API_Gateway.Services;

public class UTPickerCallerService : IUTPickerCallerService
{
    private readonly DaprClient _daprClient;
    private readonly IConfiguration _configuration;
    public ISignalRLogService SignalRLogService { get; }
    private readonly ILogger<UTGeneratorCallerService> _logger;

    public UTPickerCallerService(
        DaprClient daprClient,
        ILogger<UTGeneratorCallerService> logger,
        IConfiguration configuration,
        ISignalRLogService SignalRLogService
    )
    {
        this._daprClient = daprClient;
        this._configuration = configuration;
        this.SignalRLogService = SignalRLogService;
        this._logger = logger;
    }

    public async Task<UTPickerResponse> PickUTAsync(
        CodeProject sourceProject,
        List<CodeProject> testProjects,
        string targetLanguage
    )
    {
        this.SignalRLogService.SendToLogView("UTGEN Picking unit tests...");
        this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP1, WStates.STATE_INPROGRESS);

        UTPickerResponse utPickerResponse = await this.PickUTBaseAsync(
            sourceProject,
            testProjects.ToList(),
            targetLanguage
        );
        if (utPickerResponse.ReturnCode == GSProtoUT.ReturnCode.Success)
        {
            this.SignalRLogService.SendToLogView("UTGEN Finished picking unit tests");
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP1, WStates.STATE_COMPLETED);
            this.SignalRLogService.SendUTResult(utPickerResponse);
            return utPickerResponse;
        }
        else
        {
            // Anything other than success is an error
            this._logger.LogError("Picking unit tests failed :" + utPickerResponse.Error);
            var UTPException = new UTPException(utPickerResponse.Error);
            this.SignalRLogService.SendToLogView("UTGEN " + UTPException.UserMessage, level: "error");
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP1, WStates.STATE_ERROR);
            // Those error states still have candidate solutions
            if (
                utPickerResponse.ReturnCode == GSProtoUT.ReturnCode.FailedTestCompile
                || utPickerResponse.ReturnCode == GSProtoUT.ReturnCode.FailedTestExecution
            )
            {
                this.SignalRLogService.SendUTResult(utPickerResponse, "error");
            }
            return utPickerResponse;
        }
    }

    private async Task<UTPickerResponse> PickUTBaseAsync(
        CodeProject sourceProject,
        List<CodeProject> testProjects,
        string targetLanguage
    )
    {
        // Only these languages are supported
        string[] available_langs = ["dotnetframework", "dotnet8", "java8", "java21"];
        if (!available_langs.Contains(targetLanguage))
        {
            this._logger.LogInformation($"Picking unit tests for {targetLanguage} is not supported; returning first test project");
            return new UTPickerResponse(
                solution: testProjects[0],
                testOutput: "",
                error: "",
                returnCode: GSProtoUT.ReturnCode.Success
            );
        }

        string appId = this._configuration["Services:GoatService:AppId"] ?? String.Empty;
        if (String.IsNullOrEmpty(appId))
        {
            throw new Exception("GoatService AppId not found in configuration");
        }

        // convert the dotnet class to proto
        GSProtoUT.UTPickerRequest protoRequest =
            new()
            {
                SourceProject = sourceProject.ToProto(),
                TestProjects = { testProjects.Select(t => t.ToProto()) },
                TargetLanguage = targetLanguage
            };

        // call the dapr service
        GSProtoUT.UTPickerResponse protoResponse = await this._daprClient.InvokeMethodGrpcAsync<
            GSProtoUT.UTPickerRequest,
            GSProtoUT.UTPickerResponse
        >(appId, "pick_unittests", protoRequest);
        return new UTPickerResponse(protoResponse);
    }
}
