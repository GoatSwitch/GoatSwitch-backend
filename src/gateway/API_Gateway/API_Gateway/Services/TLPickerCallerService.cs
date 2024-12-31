using API_Gateway.Models.TLPicker;
using API_Gateway.Models.Project;
using API_Gateway.Models.Workflow;
using Dapr.Client;
using GSProtoFN = API_Gateway.Models.TLPicker.Proto;
using API_Gateway.Services.Exceptions;

namespace API_Gateway.Services;

public class TLPickerCallerService : ITLPickerCallerService
{
    private DaprClient _daprClient;
    private IConfiguration _configuration;
    public ISignalRLogService SignalRLogService { get; }
    private readonly ILogger<UTGeneratorCallerService> _logger;

    public TLPickerCallerService(
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

    public async Task<TLPickerResponse> PickAsync(
        CodeProject sourceProject,
        CodeProject testProject,
        List<CodeProject> translations,
        string targetLanguage
    )
    {
        this._logger.LogInformation("TLPicker started");
        this.SignalRLogService.SendToLogView(
            $"TLVAL Validating {targetLanguage} translation candidates against generated unit tests..."
        );
        this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP3, WStates.STATE_INPROGRESS);
        TLPickerResponse tlPickerResponse = await this.PickBaseAsync(
            sourceProject,
            testProject,
            translations,
            targetLanguage
        );
        this._logger.LogInformation("TLPicker done");

        if (tlPickerResponse.ReturnCode == GSProtoFN.ReturnCode.Success)
        {
            this.SignalRLogService.SendTranslationResult(tlPickerResponse, "info");
            this._logger.LogInformation("Best solution: {Solution}", tlPickerResponse.Solution);
            this.SignalRLogService.SendToLogView($"TLVAL {targetLanguage} code validation successful");
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP3, WStates.STATE_COMPLETED);
            return tlPickerResponse;
        }
        else
        {
            // Anything other than success is an error
            this._logger.LogError("Picking translation failed: " + tlPickerResponse.Error);
            var TLPException = new TLPException(tlPickerResponse.Error);
            this.SignalRLogService.SendToLogView($"TLVAL " + TLPException.UserMessage, level: "error");
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP3, WStates.STATE_ERROR);
            if (
                tlPickerResponse.ReturnCode == GSProtoFN.ReturnCode.FailedTestCompile
                || tlPickerResponse.ReturnCode == GSProtoFN.ReturnCode.FailedTestExecution
            )
            {
                this.SignalRLogService.SendTranslationResult(tlPickerResponse, "error");
                this._logger.LogInformation("Best failed translation: {Solution}", tlPickerResponse.Solution);
                this._logger.LogInformation("Best failed translation output: {Solution}", tlPickerResponse.TestOutput);
            }
            return tlPickerResponse;
        }
    }

    public async Task<TLPickerResponse> PickBaseAsync(
        CodeProject sourceProject,
        CodeProject testProject,
        List<CodeProject> translations,
        string targetLanguage
    )
    {
        // log target language
        this._logger.LogInformation("Target language: {TargetLanguage}", targetLanguage);
        string appId = this._configuration["Services:GoatService:AppId"] ?? String.Empty;
        if (String.IsNullOrEmpty(appId))
        {
            throw new Exception("GoatService AppId not found in configuration");
        }
        // convert the dotnet class to proto
        GSProtoFN.TLPickerRequest protoRequest =
            new()
            {
                SourceProject = sourceProject.ToProto(),
                TargetLanguage = targetLanguage,
                TestProject = testProject.ToProto(),
                Translations = { translations.Select(t => t.ToProto()) }
            };
        // call the dapr service
        GSProtoFN.TLPickerResponse protoResponse = await this._daprClient.InvokeMethodGrpcAsync<
            GSProtoFN.TLPickerRequest,
            GSProtoFN.TLPickerResponse
        >(appId, "pick_translation", protoRequest);
        return new TLPickerResponse(protoResponse);
    }
}
