using System.Text.Json.Serialization;
using API_Gateway.Models.Project;

namespace API_Gateway.Models.UTGenerator;

using GSProtoUT = API_Gateway.Models.UTGenerator.Proto;

public class UTGeneratorResponse
{
    [JsonPropertyName("solutions")]
    public List<CodeProject> Solutions { get; set; }

    [JsonPropertyName("error")]
    public string Error { get; set; }

    [JsonPropertyName("return_code")]
    public GSProtoUT.ReturnCode ReturnCode { get; set; }

    public UTGeneratorResponse(GSProtoUT.UTGeneratorResponse protoResponse)
    {
        this.Solutions = protoResponse.Solutions.Select(s => CodeProject.FromProto(s)).ToList();
        this.Error = protoResponse.Error;
        this.ReturnCode = protoResponse.ReturnCode;
    }
}
