using System.Reflection.Emit;
using System.Text.Json.Serialization;

namespace API_Gateway.Models.Project;

using GSProto = API_Gateway.Models.Proto;

public class CodeProject
{
    [JsonPropertyName("display_name")]
    public string DisplayName { get; set; }

    [JsonPropertyName("files")]
    public List<CodeFile> Files { get; set; }

    [JsonPropertyName("reference_files")]
    public List<CodeFile> ReferenceFiles { get; set; }

    [JsonPropertyName("source_language")]
    public string SourceLanguage { get; set; }

    public CodeProject()
    {
        this.DisplayName = "";
        this.Files = [];
        this.ReferenceFiles = [];
        this.SourceLanguage = "";
    }

    public CodeProject(
        List<CodeFile> files,
        string sourceLanguage,
        string? displayName = null,
        List<CodeFile>? referenceFiles = null
    )
    {
        this.Files = files;
        this.SourceLanguage = sourceLanguage;
        this.DisplayName = displayName ?? "";
        this.ReferenceFiles = referenceFiles ?? [];
        // set default input name to filename if not specified
        // filename is the full path of the file, so we need to extract the name
        if (displayName == "" && this.Files.Count > 0)
        {
            // consider os file path separator and extract the last part of the path
            this.DisplayName = this.Files[0].FileName.Split(Path.DirectorySeparatorChar).Last();
        }
    }

    public override string ToString()
    {
        return $"CodeProject: {this.DisplayName} ({this.SourceLanguage}) with {this.Files.Count} files and {this.ReferenceFiles.Count} reference files";
    }

    public GSProto.CodeProject ToProto()
    {
        return new GSProto.CodeProject()
        {
            DisplayName = this.DisplayName ?? "",
            SourceLanguage = this.SourceLanguage,
            Files = { this.Files.Select(f => f.ToProto()) },
            ReferenceFiles = { this.ReferenceFiles.Select(f => f.ToProto()) }
        };
    }

    public static CodeProject FromProto(GSProto.CodeProject proto)
    {
        return new CodeProject(
            proto.Files.Select(f => CodeFile.FromProto(f)).ToList(),
            proto.SourceLanguage,
            proto.DisplayName,
            proto.ReferenceFiles.Select(f => CodeFile.FromProto(f)).ToList()
        );
    }
}
