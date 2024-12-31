using API_Gateway.Models.Project;
using API_Gateway.Models.TLGenerator;

namespace API_Gateway.Services;

public interface ITLGeneratorCallerService
{
    public ISignalRLogService SignalRLogService { get; }
    Task<TLGeneratorResponse> GenerateTLAsync(
        CodeProject sourceProject,
        string targetLanguage,
        string model = "default",
        string instruction = ""
    );
    Task<TLGeneratorResponse> AssessAsync(
        CodeProject sourceProject,
        string targetLanguage,
        string model = "assess",
        string instruction = ""
    );
}
