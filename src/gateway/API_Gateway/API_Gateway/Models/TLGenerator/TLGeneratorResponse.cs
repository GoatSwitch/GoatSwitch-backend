using System.Text.Json.Serialization;
using API_Gateway.Models.Project;

namespace API_Gateway.Models.TLGenerator;

using GSProtoTL = API_Gateway.Models.TLGenerator.Proto;

public class TLGeneratorResponse
{
    [JsonPropertyName("solutions")]
    public List<CodeProject> Solutions { get; set; }

    [JsonPropertyName("error")]
    public string Error { get; set; }

    [JsonPropertyName("return_code")]
    public GSProtoTL.ReturnCode ReturnCode { get; set; }

    public TLGeneratorResponse(GSProtoTL.TLGeneratorResponse protoResponse)
    {
        this.Solutions = protoResponse.Solutions.Select(s => CodeProject.FromProto(s)).ToList();
        this.Error = protoResponse.Error;
        this.ReturnCode = protoResponse.ReturnCode;
    }
}
