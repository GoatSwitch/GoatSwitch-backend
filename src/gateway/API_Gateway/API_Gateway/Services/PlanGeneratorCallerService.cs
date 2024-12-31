using API_Gateway.Models.Project;
using API_Gateway.Models.TLGenerator;
using API_Gateway.Models.Workflow;
using API_Gateway.Services.Exceptions;
using Dapr.Client;
using GSProtoTLGen = API_Gateway.Models.TLGenerator.Proto;

namespace API_Gateway.Services;

public class PlanGeneratorCallerService(
    DaprClient daprClient,
    ILogger<UTGeneratorCallerService> logger,
    IConfiguration configuration,
    ISignalRLogService SignalRLogService
    ) : IPlanGeneratorCallerService
{
    private DaprClient _daprClient = daprClient;
    private IConfiguration _configuration = configuration;
    public ISignalRLogService SignalRLogService { get; } = SignalRLogService;
    private readonly ILogger<UTGeneratorCallerService> _logger = logger;

    public async Task<PlanGeneratorResponse> GeneratePlanAsync(
        CodeProject sourceProject,
        string targetLanguage,
        string instruction = ""
    )
    {
        string msg = $"PLANGEN Generating plan for {sourceProject.DisplayName} ({targetLanguage})";
        this.SignalRLogService.SendToLogView(msg);
        this._logger.LogInformation(msg + $" with instruction: {instruction}");
        this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP2, WStates.STATE_INPROGRESS);
        PlanGeneratorResponse planGeneratorResponse = await this.BaseAsync(
            sourceProject,
            targetLanguage: targetLanguage,
            instruction: instruction,
            remote_function: "generate_plan"
        );
        if (planGeneratorResponse.ReturnCode == GSProtoTLGen.ReturnCode.Success)
        {
            this.SignalRLogService.SendToLogView($"PLANGEN Finished {targetLanguage} plan...");
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP2, WStates.STATE_COMPLETED);
            return planGeneratorResponse;
        }
        else
        {
            this.SignalRLogService.SendProgressUpdate(WSteps.KEY_STEP2, WStates.STATE_ERROR);
            this._logger.LogError("Generating plan failed " + planGeneratorResponse.Error);
            var exception = new PlanGException(planGeneratorResponse.Error);
            this.SignalRLogService.SendToLogView("PLANGEN " + exception.UserMessage, level: "error");
            throw exception;
        }
    }

    private async Task<PlanGeneratorResponse> BaseAsync(
        CodeProject sourceProject,
        string targetLanguage,
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
        GSProtoTLGen.TLGeneratorRequest protoRequest =
            new()
            {
                SourceProject = sourceProject.ToProto(),
                Instruction = instruction,
                TargetLanguage = targetLanguage
            };
        double req_size = Math.Round((double)protoRequest.CalculateSize() / 1024 / 1024, 2);
        this._logger.LogInformation($"Request size in MB: {req_size}");

        // call the dapr service
        GSProtoTLGen.PlanGeneratorResponse protoResponse;
        try
        {
            protoResponse = await this._daprClient.InvokeMethodGrpcAsync<
                GSProtoTLGen.TLGeneratorRequest,
                GSProtoTLGen.PlanGeneratorResponse
                >(appId, remote_function, protoRequest);
        }
        catch (Exception e)
        {
            protoResponse = new GSProtoTLGen.PlanGeneratorResponse
            {
                ReturnCode = GSProtoTLGen.ReturnCode.Failed,
                Error = e.Message
            };
        }
        double res_size = Math.Round((double)protoResponse.CalculateSize() / 1024 / 1024, 2);
        this._logger.LogInformation($"Response size in MB: {res_size}");
        return new PlanGeneratorResponse(protoResponse);
    }
}
