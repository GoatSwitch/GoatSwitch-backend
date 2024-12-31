using System.Text.Json.Serialization;

namespace API_Gateway.Models.TLGenerator;

using GSProtoTL = API_Gateway.Models.TLGenerator.Proto;

public class AIPlan
{

    [JsonPropertyName("operations")]
    public List<Operation> Operations { get; set; } = [];

    public AIPlan() { }

    public GSProtoTL.AIPlan ToProto()
    {
        return new GSProtoTL.AIPlan() { Operations = { this.Operations.Select(s => s.ToProto()).ToList() } };
    }

    public static AIPlan FromProto(GSProtoTL.AIPlan proto)
    {
        return new AIPlan() { Operations = proto.Operations.Select(s => Operation.FromProto(s)).ToList() };
    }

    public override string ToString()
    {
        /* eg:
        # AI Plan
        ## Step 1: upgrade dotnet project
        Upgrade the project to .Net 8
        */
        if (this.Operations.Count == 0)
        {
            throw new Exception("No operations in AI Plan");
        }
        string result = "# AI Plan\n";
        for (int i = 0; i < this.Operations.Count; i++)
        {
            Operation operation = this.Operations[i];
            // change all caps operation names to user-friendly names for frontend
            string user_friendly_operation_name = operation.OperationName.ToLower().Replace("_", " ");
            result += $"## Step {i + 1}: {user_friendly_operation_name}\n{operation.Description}\n";
        }
        return result;
    }

    public static AIPlan FromString(string planString)
    {
        // split by newline
        string[] lines = planString.Split("\n");
        AIPlan currentPlan = new();
        string descriptionAccumulator = "";

        // iterate through the lines
        for (int i = 1; i < lines.Length; i++)
        {
            // check if the line starts with "## Step"
            if (lines[i].StartsWith("## Step"))
            {
                // if there is an accumulated description, set it to the last operation
                if (descriptionAccumulator != "" && currentPlan.Operations.Count > 0)
                {
                    currentPlan.Operations.Last().Description = descriptionAccumulator.Trim();
                    descriptionAccumulator = "";
                }

                // parse the operation name
                string operationName = lines[i].Split(":")[1].Trim().ToUpper().Replace(" ", "_");
                // create new operation
                Operation operation = new Operation(operationName, "");
                currentPlan.Operations.Add(operation);
            }
            // check not empty line and operations not empty
            else if (lines[i].Trim() != "")
            {
                // accumulate description lines
                descriptionAccumulator += lines[i] + "\n";
            }
        }

        // set the accumulated description to the last operation if any
        if (descriptionAccumulator != "" && currentPlan.Operations.Count > 0)
        {
            currentPlan.Operations.Last().Description = descriptionAccumulator.Trim();
        }

        if (currentPlan.Operations.Count == 0)
        {
            throw new Exception($"Failed to parse AI Plan from string: {planString}");
        }
        return currentPlan;
    }
}

public class Operation
{
    [JsonPropertyName("operation_name")]
    public string OperationName { get; set; }

    [JsonPropertyName("description")]
    public string Description { get; set; }

    public Operation(string operationName, string description)
    {
        this.OperationName = operationName;
        this.Description = description;
    }

    public GSProtoTL.Operation ToProto()
    {
        return new GSProtoTL.Operation() { OperationName = this.OperationName, Description = this.Description };
    }

    public static Operation FromProto(GSProtoTL.Operation proto)
    {
        return new Operation(proto.OperationName, proto.Description);
    }
}
