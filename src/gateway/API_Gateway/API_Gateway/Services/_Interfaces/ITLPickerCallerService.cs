using API_Gateway.Models.TLPicker;
using API_Gateway.Models.Project;

namespace API_Gateway.Services;

public interface ITLPickerCallerService
{
    public ISignalRLogService SignalRLogService { get; }
    Task<TLPickerResponse> PickAsync(
        CodeProject sourceProject,
        CodeProject testProject,
        List<CodeProject> translations,
        string targetLanguage
    );
}
