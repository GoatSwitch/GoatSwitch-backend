using System.Text.Json.Serialization;
using API_Gateway.Models.Project;

namespace API_Gateway.Models.TLPicker;

using GSProtoFN = API_Gateway.Models.TLPicker.Proto;

public class TLPickerResponse
{
    [JsonPropertyName("solution")]
    public CodeProject Solution { get; set; }

    [JsonPropertyName("test_output")]
    public string TestOutput { get; set; }

    [JsonPropertyName("error")]
    public string Error { get; set; }

    [JsonPropertyName("return_code")]
    public GSProtoFN.ReturnCode ReturnCode { get; set; }

    public TLPickerResponse(GSProtoFN.TLPickerResponse protoResponse)
    {
        this.Solution = CodeProject.FromProto(protoResponse.Solution);
        this.Error = protoResponse.Error;
        this.ReturnCode = protoResponse.ReturnCode;
        this.TestOutput = protoResponse.TestOutput;
    }

    public TLPickerResponse(CodeProject solution, string error, GSProtoFN.ReturnCode returnCode, string testOutput)
    {
        this.Solution = solution;
        this.Error = error;
        this.ReturnCode = returnCode;
        this.TestOutput = testOutput;
    }
}
