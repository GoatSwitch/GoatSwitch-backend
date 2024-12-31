using API_Gateway.Models.Project;
using API_Gateway.Models.UTGenerator;

namespace API_Gateway.Services;

public interface IUTGeneratorCallerService
{
    public ISignalRLogService SignalRLogService { get; }
    Task<UTGeneratorResponse> GenerateUTAsync(
        CodeProject source_project,
        CodeProject? testProject,
        string targetLanguage,
        string instruction = ""
    );
}
