using API_Gateway.Models.Project;
using API_Gateway.Models.TLGenerator;

namespace API_Gateway.Services;

public interface IPlanGeneratorCallerService
{
    public ISignalRLogService SignalRLogService { get; }
    Task<PlanGeneratorResponse> GeneratePlanAsync(
        CodeProject sourceProject,
        string targetLanguage,
        string instruction = ""
    );
}
