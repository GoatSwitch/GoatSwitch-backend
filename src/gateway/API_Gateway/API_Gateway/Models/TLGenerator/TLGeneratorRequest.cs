using System.Text.Json.Serialization;
using API_Gateway.Models.Project;

namespace API_Gateway.Models.TLGenerator;

// TODO: these fields are wrong; but request classes are never really used; instead proto is constructed in callerserivces
// what is the right way?
public class TLGeneratorRequest(CodeProject sourceProject, string targetLanguage)
{
    [JsonPropertyName("source_project")]
    public CodeProject SourceProject { get; set; } = sourceProject;

    [JsonPropertyName("target_language")]
    public string TargetLanguage { get; set; } = targetLanguage;
}
