using System.Text.Json.Serialization;
using API_Gateway.Models.Project;

namespace API_Gateway.Models.TLPicker;

public class TLPickerRequest
{
    [JsonPropertyName("source_project")]
    public CodeProject SourceProject { get; set; }

    [JsonPropertyName("translated_projects")]
    public List<CodeProject> Translations { get; set; }

    [JsonPropertyName("test_project")]
    public CodeProject TestProject { get; set; }

    [JsonPropertyName("target_language")]
    public string TargetLanguage { get; set; }

    public TLPickerRequest(
        CodeProject sourceProject,
        List<CodeProject> translations,
        CodeProject testProject,
        string targetLanguage
    )
    {
        this.SourceProject = sourceProject;
        this.Translations = translations;
        this.TestProject = testProject;
        this.TargetLanguage = targetLanguage;
    }
}
