using System.Text.Json;
using System.Text.Json.Serialization;
using API_Gateway.Models.Project;

namespace API_Gateway.Models.UTPicker;

public class UTPickerRequest
{
    [JsonPropertyName("source_project")]
    public CodeProject SourceProject { get; set; }

    [JsonPropertyName("test_projects")]
    public List<CodeProject> TestProjects { get; set; }

    [JsonPropertyName("target_language")]
    public string TargetLanguage { get; set; }

    public UTPickerRequest(CodeProject sourceProject, List<CodeProject> testProjects, string targetLanguage)
    {
        this.SourceProject = sourceProject;
        this.TargetLanguage = targetLanguage;
        this.TestProjects = testProjects;
    }
}
