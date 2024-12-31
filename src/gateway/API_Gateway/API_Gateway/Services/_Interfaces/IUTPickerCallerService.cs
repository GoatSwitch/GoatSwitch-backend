using API_Gateway.Models.Project;
using API_Gateway.Models.UTPicker;

namespace API_Gateway.Services;

public interface IUTPickerCallerService
{
    public ISignalRLogService SignalRLogService { get; }
    Task<UTPickerResponse> PickUTAsync(
        CodeProject source_project,
        List<CodeProject> test_projects,
        string targetLanguage
    );
}
