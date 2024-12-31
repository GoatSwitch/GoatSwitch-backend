using API_Gateway.Models.TLPicker;
using API_Gateway.Models.Project;
using API_Gateway.Models.TLGenerator;
using API_Gateway.Models.UTPicker;

namespace API_Gateway.Services
{
    public interface ISignalRLogService
    {
        public event Action<string, string>? SendToTerminalEvent;

        public event Action<string, string>? SendProgressUpdateEvent;
        public event Action<string, string>? SendToLogViewEvent;
        public event Action<List<CodeProject>, string>? SendUTCandidatesEvent;
        public event Action<UTPickerResponse, string>? SendUTResultEvent;
        public event Action<TLGeneratorResponse, string>? SendTranslationCandidatesEvent;
        public event Action<TLPickerResponse, string>? SendTranslationResultEvent;
        public event Action<TLGeneratorResponse, string>? SendAssessmentResultEvent;
        public void SendProgressUpdate(string key, string progressState);
        public void SendToLogView(string message, string level = "info");
        public void SendUTCandidates(List<CodeProject> solutionCandidates, string level = "info");
        public void SendUTResult(UTPickerResponse resp, string level = "info");
        public void SendTranslationCandidates(TLGeneratorResponse resp, string level = "info");
        public void SendTranslationResult(TLPickerResponse resp, string level = "info");
        public void SendAssessmentResult(TLGeneratorResponse resp, string level = "info");
    }
}
