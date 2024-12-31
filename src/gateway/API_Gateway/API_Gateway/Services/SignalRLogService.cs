using API_Gateway.Models.TLPicker;
using API_Gateway.Models.Project;
using API_Gateway.Models.TLGenerator;
using API_Gateway.Models.UTPicker;

namespace API_Gateway.Services;

public class SignalRLogService : ISignalRLogService
{
    private readonly ILogger<SignalRLogService> _logger;
    public event Action<string, string>? SendToTerminalEvent;
    public event Action<string, string>? SendProgressUpdateEvent;
    public event Action<string, string>? SendToLogViewEvent;
    public event Action<List<CodeProject>, string>? SendUTCandidatesEvent;
    public event Action<UTPickerResponse, string>? SendUTResultEvent;
    public event Action<TLGeneratorResponse, string>? SendTranslationCandidatesEvent;
    public event Action<TLPickerResponse, string>? SendTranslationResultEvent;
    public event Action<TLGeneratorResponse, string>? SendAssessmentResultEvent;

    public SignalRLogService(ILogger<SignalRLogService> logger)
    {
        this._logger = logger;
    }

    private string ValidateLevel(string level)
    {
        var validLevels = new HashSet<string> { "info", "error", "warning", "debug" };
        bool isValidLevel = validLevels.Contains(level);
        if (!isValidLevel)
        {
            this._logger.LogError($"Invalid log level: {level}");
        }
        return isValidLevel ? level : "info";
    }

    public void SendProgressUpdate(string key, string progressState)
    {
        this.SendProgressUpdateEvent?.Invoke(key, progressState);
    }

    public void SendToLogView(string message, string level = "info")
    {
        level = ValidateLevel(level);
        this.SendToLogViewEvent?.Invoke(message, level);
    }

    public void SendUTCandidates(List<CodeProject> solutionCandidates, string level = "info")
    {
        level = ValidateLevel(level);
        this.SendUTCandidatesEvent?.Invoke(solutionCandidates, level);
    }

    public void SendUTResult(UTPickerResponse resp, string level = "info")
    {
        level = ValidateLevel(level);
        this.SendUTResultEvent?.Invoke(resp, level);
    }

    public void SendTranslationCandidates(TLGeneratorResponse resp, string level = "info")
    {
        level = ValidateLevel(level);
        this.SendTranslationCandidatesEvent?.Invoke(resp, level);
    }

    public void SendTranslationResult(TLPickerResponse resp, string level = "info")
    {
        level = ValidateLevel(level);
        this.SendTranslationResultEvent?.Invoke(resp, level);
    }

    public void SendAssessmentResult(TLGeneratorResponse resp, string level = "info")
    {
        level = ValidateLevel(level);
        this.SendAssessmentResultEvent?.Invoke(resp, level);
    }
}
