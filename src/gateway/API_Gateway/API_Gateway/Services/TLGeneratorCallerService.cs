using API_Gateway.Models.Project;
using API_Gateway.Models.TLGenerator;
using API_Gateway.Models.Workflow;
using API_Gateway.Services.Exceptions;
using Dapr.Client;
using GSProtoTL = API_Gateway.Models.TLGenerator.Proto;

namespace API_Gateway.Services;

public class TLGeneratorCallerService(
    DaprClient daprClient,
    ILogger<UTGeneratorCallerService> logger,
    IConfiguration configuration,
    ISignalRLogService SignalRLogService
    ) : ITLGeneratorCallerService
{
    private DaprClient _daprClient = daprClient;
    private IConfiguration _configuration = configuration;
    public ISignalRLogService SignalRLogService { get; } = SignalRLogService;
    private readonly ILogger<UTGeneratorCallerService> _logger = logger;

    public async Task<TLGeneratorResponse> GenerateTLAsync(
        CodeProject sourceProject,
        string targetLanguage,
        string model = "default",
        string instruction = ""
    )
    {
        string msg = $"Translating code to language {targetLanguage}...";
        this.SignalRLogService.SendToLogView($"TLGEN {msg}");
        this._logger.LogInformation(msg);
        this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP2, WStates.STATE_INPROGRESS);
        TLGeneratorResponse tlGeneratorResponse = await this.BaseAsync(
            sourceProject,
            targetLanguage,
            model,
            instruction,
            "generate_translations"
        );
        if (tlGeneratorResponse.ReturnCode == GSProtoTL.ReturnCode.Success)
        {
            this.SignalRLogService.SendTranslationCandidates(tlGeneratorResponse, "info");
            this.SignalRLogService.SendToLogView($"TLGEN Finished {targetLanguage} translation candidates...");
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP2, WStates.STATE_COMPLETED);
            return tlGeneratorResponse;
        }
        else
        {
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP2, WStates.STATE_ERROR);
            this._logger.LogError("Generating translations failed :" + tlGeneratorResponse.Error);
            var exception = new TLGException(tlGeneratorResponse.Error);
            this.SignalRLogService.SendToLogView("TLGEN " + exception.UserMessage, level: "error");
            throw exception;
        }
    }

    public async Task<TLGeneratorResponse> AssessAsync(
        CodeProject sourceProject,
        string targetLanguage,
        string model = "assess",
        string instruction = ""
    )
    {
        this.SignalRLogService.SendToLogView($"PLANGEN Assessing source project...");
        string msg = $"Assessing source project...";
        this._logger.LogInformation(msg);
        TLGeneratorResponse tlGeneratorResponse = await this.BaseAsync(sourceProject, targetLanguage, "", "", "assess");
        if (tlGeneratorResponse.Solutions == null || !tlGeneratorResponse.Solutions.Any())
        {
            if (string.IsNullOrEmpty(tlGeneratorResponse.Error))
            {
                tlGeneratorResponse.Error = "No error message provided, but no assessment was returned";
            }
            this.SignalRLogService.SendToLogView(
                "PLANGEN Error occurred while assessing source project\n",
                level: "error"
            );
            throw new Exception("Assessing source project failed " + tlGeneratorResponse.Error);
        }
        this.SignalRLogService.SendToLogView($"PLANGEN Finished assessing source project...");
        this.SignalRLogService.SendAssessmentResult(tlGeneratorResponse, "info");
        return tlGeneratorResponse;
    }

    private async Task<TLGeneratorResponse> BaseAsync(
        CodeProject sourceProject,
        string targetLanguage,
        string model,
        string instruction,
        string remote_function
    )
    {
        string appId = this._configuration["Services:GoatService:AppId"] ?? String.Empty;
        if (String.IsNullOrEmpty(appId))
        {
            throw new Exception("GoatService AppId not found in configuration");
        }
        // convert the dotnet class to proto
        GSProtoTL.TLGeneratorRequest protoRequest =
            new()
            {
                SourceProject = sourceProject.ToProto(),
                TargetLanguage = targetLanguage,
                Model = model,
                Instruction = instruction
            };
        double req_size = Math.Round((double)protoRequest.CalculateSize() / 1024 / 1024, 2);
        this._logger.LogInformation($"Request size in MB: {req_size}");

        // call the dapr service
        GSProtoTL.TLGeneratorResponse protoResponse;
        try
        {
            protoResponse = await this._daprClient.InvokeMethodGrpcAsync<
                GSProtoTL.TLGeneratorRequest,
                GSProtoTL.TLGeneratorResponse
                >(appId, remote_function, protoRequest);
        }
        catch (Exception e)
        {
            protoResponse = new GSProtoTL.TLGeneratorResponse
            {
                ReturnCode = GSProtoTL.ReturnCode.Failed,
                Error = e.Message
            };
        }
        double res_size = Math.Round((double)protoResponse.CalculateSize() / 1024 / 1024, 2);
        this._logger.LogInformation($"Response size in MB: {res_size}");
        return new TLGeneratorResponse(protoResponse);
    }
}
