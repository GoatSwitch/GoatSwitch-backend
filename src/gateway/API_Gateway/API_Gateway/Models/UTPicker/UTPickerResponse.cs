using System.Text.Json.Serialization;
using API_Gateway.Models.Project;

namespace API_Gateway.Models.UTPicker;

using GSProtoUT = API_Gateway.Models.UTPicker.Proto;

public class UTPickerResponse
{
    [JsonPropertyName("solution")]
    public CodeProject Solution { get; set; }

    [JsonPropertyName("test_output")]
    public string TestOutput { get; set; }

    [JsonPropertyName("error")]
    public string Error { get; set; }

    [JsonPropertyName("return_code")]
    public GSProtoUT.ReturnCode ReturnCode { get; set; }

    public UTPickerResponse(GSProtoUT.UTPickerResponse response)
    {
        this.Solution = CodeProject.FromProto(response.Solution);
        this.TestOutput = response.TestOutput;
        this.Error = response.Error;
        this.ReturnCode = response.ReturnCode;
    }

    public UTPickerResponse(CodeProject solution, string testOutput, string error, GSProtoUT.ReturnCode returnCode)
    {
        this.Solution = solution;
        this.TestOutput = testOutput;
        this.Error = error;
        this.ReturnCode = returnCode;
    }
}
