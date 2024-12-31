namespace API_Gateway.Models.Project;

using System.Text.Json.Serialization;
using GSProto = API_Gateway.Models.Proto;

public class CodeFile
{
    [JsonPropertyName("file_name")]
    public string FileName { get; set; }

    [JsonPropertyName("source_code")]
    public string SourceCode { get; set; }

    public CodeFile(string fileName, string sourceCode)
    {
        this.FileName = fileName;
        this.SourceCode = sourceCode;
    }

    public GSProto.CodeFile ToProto()
    {
        return new GSProto.CodeFile() { FileName = this.FileName, SourceCode = this.SourceCode };
    }

    public static CodeFile FromProto(GSProto.CodeFile proto)
    {
        return new CodeFile(proto.FileName, proto.SourceCode);
    }
}
