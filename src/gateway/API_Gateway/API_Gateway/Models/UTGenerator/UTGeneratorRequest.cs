using System.Text.Json;
using System.Text.Json.Serialization;
using API_Gateway.Models.Project;

namespace API_Gateway.Models.UTGenerator;

public class UTGeneratorRequest
{
    [JsonPropertyName("source_project")]
    public CodeProject SourceProject { get; set; }

    [JsonPropertyName("target_language")]
    public string TargetLanguage { get; set; }

    [JsonPropertyName("test_project")]
    public CodeProject? TestProject { get; set; }

    [JsonPropertyName("instruction")]
    public string Instruction { get; set; }

    public UTGeneratorRequest(
        CodeProject sourceProject,
        string targetLanguage,
        CodeProject? testProject = null,
        string instruction = ""
    )
    {
        this.SourceProject = sourceProject;
        this.TargetLanguage = targetLanguage;
        this.TestProject = testProject;
        this.Instruction = instruction;
    }
}
