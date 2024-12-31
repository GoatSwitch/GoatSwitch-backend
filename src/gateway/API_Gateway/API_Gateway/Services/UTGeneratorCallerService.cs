using API_Gateway.Models.Project;
using API_Gateway.Models.UTGenerator;
using API_Gateway.Models.Workflow;
using API_Gateway.Services.Exceptions;
using Dapr.Client;
using GSProtoUT = API_Gateway.Models.UTGenerator.Proto;

namespace API_Gateway.Services;

public class UTGeneratorCallerService : IUTGeneratorCallerService
{
    private readonly ILogger<UTGeneratorCallerService> _logger;
    private readonly DaprClient _daprClient;
    private readonly IConfiguration _configuration;
    public ISignalRLogService SignalRLogService { get; }

    public UTGeneratorCallerService(
        DaprClient daprClient,
        ILogger<UTGeneratorCallerService> logger,
        IConfiguration configuration,
        ISignalRLogService SignalRLogService
    )
    {
        this._daprClient = daprClient;
        this._configuration = configuration;
        this._logger = logger;
        this.SignalRLogService = SignalRLogService;
    }

    public async Task<UTGeneratorResponse> GenerateUTAsync(
        CodeProject sourceProject,
        CodeProject? testProject,
        string targetLanguage,
        string instruction = ""
    )
    {
        this.SignalRLogService.SendToLogView("UTGEN Generating unit tests candidates...");
        this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP1, WStates.STATE_INPROGRESS);
        UTGeneratorResponse utGenResponse = await GenerateUTBaseAsync(
            sourceProject,
            testProject: testProject,
            targetLanguage: targetLanguage,
            instruction: instruction
        );
        if (utGenResponse.ReturnCode == GSProtoUT.ReturnCode.Success)
        {
            this.SignalRLogService.SendUTCandidates(utGenResponse.Solutions);
            this.SignalRLogService.SendToLogView("UTGEN Finished generating unit test candidates");
            return utGenResponse;
        }
        else
        {
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP1, WStates.STATE_ERROR);
            this._logger.LogError("Generating unit tests failed :" + utGenResponse.Error);
            var exception = new UTGException(utGenResponse.Error);
            this.SignalRLogService.SendToLogView("UTGEN " + exception.UserMessage, level: "error");
            throw exception;
        }
    }

    public async Task<UTGeneratorResponse> GenerateUTBaseAsync(
        CodeProject sourceProject,
        CodeProject? testProject,
        string targetLanguage,
        string instruction
    )
    {
        string appId = this._configuration["Services:GoatService:AppId"] ?? String.Empty;
        if (String.IsNullOrEmpty(appId))
        {
            throw new Exception("GoatService AppId not found in configuration");
        }

        // make empty test project if not provided
        testProject ??= new CodeProject();

        // convert the dotnet class to proto
        GSProtoUT.UTGeneratorRequest protoRequest =
            new()
            {
                SourceProject = sourceProject.ToProto(),
                TestProject = testProject.ToProto(),
                TargetLanguage = targetLanguage,
                Instruction = instruction
            };
        // log the size of the request
        double req_size = Math.Round((double)protoRequest.CalculateSize() / 1024 / 1024, 2);
        this._logger.LogInformation($"Request size in MB: {req_size}");

        // call the dapr service
        GSProtoUT.UTGeneratorResponse protoResponse;
        try
        {
            protoResponse = await this._daprClient.InvokeMethodGrpcAsync<
                GSProtoUT.UTGeneratorRequest,
                GSProtoUT.UTGeneratorResponse
                >(appId, "generate_unittests", protoRequest);
        }
        catch (Exception e)
        {
            protoResponse = new GSProtoUT.UTGeneratorResponse
            {
                ReturnCode = GSProtoUT.ReturnCode.Failed,
                Error = e.Message
            };

        }
        return new UTGeneratorResponse(protoResponse);
    }
}
