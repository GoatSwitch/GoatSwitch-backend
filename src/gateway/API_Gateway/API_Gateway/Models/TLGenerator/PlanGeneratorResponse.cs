using System.Text.Json.Serialization;

namespace API_Gateway.Models.TLGenerator;

using GSProtoTL = API_Gateway.Models.TLGenerator.Proto;

public class PlanGeneratorResponse
{
    [JsonPropertyName("plan")]
    public AIPlan Plan { get; set; }

    [JsonPropertyName("error")]
    public string Error { get; set; }

    [JsonPropertyName("return_code")]
    public GSProtoTL.ReturnCode ReturnCode { get; set; }

    public PlanGeneratorResponse(GSProtoTL.PlanGeneratorResponse protoResponse)
    {
        this.Plan = AIPlan.FromProto(protoResponse.Plan);
        this.Error = protoResponse.Error;
        this.ReturnCode = protoResponse.ReturnCode;
    }
    public static PlanGeneratorResponse FromProto(GSProtoTL.PlanGeneratorResponse protoResponse)
    {
        return new PlanGeneratorResponse(protoResponse);
    }

    public GSProtoTL.PlanGeneratorResponse ToProto()
    {
        return new GSProtoTL.PlanGeneratorResponse() { Plan = this.Plan.ToProto(), Error = this.Error, ReturnCode = this.ReturnCode };
    }

}