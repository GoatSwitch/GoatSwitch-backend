using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;
using API_Gateway.Models.TLGenerator;
using GSProtoTL = API_Gateway.Models.TLGenerator.Proto;

public class AIPlanTest
{
    [Fact]
    public void ToProto_ShouldConvertToProtoCorrectly()
    {
        // Arrange
        var operations = new List<Operation>
        {
            new Operation("Operation1", "Description1"),
            new Operation("Operation2", "Description2")
        };
        var aiPlan = new AIPlan { Operations = operations };

        // Act
        var proto = aiPlan.ToProto();

        // Assert
        Assert.Equal(2, proto.Operations.Count);
        Assert.Equal("Operation1", proto.Operations[0].OperationName);
        Assert.Equal("Description1", proto.Operations[0].Description);
        Assert.Equal("Operation2", proto.Operations[1].OperationName);
        Assert.Equal("Description2", proto.Operations[1].Description);
    }

    [Fact]
    public void FromProto_ShouldConvertFromProtoCorrectly()
    {
        // Arrange
        var protoOperations = new List<GSProtoTL.Operation>
        {
            new GSProtoTL.Operation { OperationName = "Operation1", Description = "Description1" },
            new GSProtoTL.Operation { OperationName = "Operation2", Description = "Description2" }
        };
        var proto = new GSProtoTL.AIPlan { Operations = { protoOperations } };

        // Act
        var aiPlan = AIPlan.FromProto(proto);

        // Assert
        Assert.Equal(2, aiPlan.Operations.Count);
        Assert.Equal("Operation1", aiPlan.Operations[0].OperationName);
        Assert.Equal("Description1", aiPlan.Operations[0].Description);
        Assert.Equal("Operation2", aiPlan.Operations[1].OperationName);
        Assert.Equal("Description2", aiPlan.Operations[1].Description);
    }

    [Fact]
    public void ToString_ShouldConvertToStringCorrectly()
    {
        // Arrange
        var operations = new List<Operation>
        {
            new Operation("OPERATION_ONE", "Description1\nanotherline\nanotherline"),
            new Operation("OPERATION_TWO", "Description2\nabc")
        };
        var aiPlan = new AIPlan { Operations = operations };
        var expectedString = "# AI Plan\n## Step 1: operation one\nDescription1\nanotherline\nanotherline\n## Step 2: operation two\nDescription2\nabc\n";

        // Act
        var resultString = aiPlan.ToString();

        // Assert
        Assert.Equal(expectedString, resultString);
    }

    [Fact]
    public void FromString_ShouldConvertFromStringCorrectly()
    {
        // Arrange
        var planString = "# AI Plan\n## Step 1: operation one\nDescription1\nanotherline\nanotherline\n## Step 2: operation two\nDescription2\nabc\n";
        var expectedOperations = new List<Operation>
        {
            new Operation("OPERATION_ONE", "Description1\nanotherline\nanotherline"),
            new Operation("OPERATION_TWO", "Description2\nabc")
        };

        // Act
        var aiPlan = AIPlan.FromString(planString);

        // Assert
        Assert.Equal(2, aiPlan.Operations.Count);
        Assert.Equal(expectedOperations[0].OperationName, aiPlan.Operations[0].OperationName);
        Assert.Equal(expectedOperations[0].Description, aiPlan.Operations[0].Description);
        Assert.Equal(expectedOperations[1].OperationName, aiPlan.Operations[1].OperationName);
        Assert.Equal(expectedOperations[1].Description, aiPlan.Operations[1].Description);
    }

    [Fact]
    public void FromString_ShouldThrowExceptionWhenNoOperations()
    {
        // Arrange
        var planString = "# AI Plan\n# Step 1: Operation1\nDescription1\n# Step 2: Operation2\nDescription2\n";

        // Act
        Action act = () => AIPlan.FromString(planString);

        // Assert
        var exception = Assert.Throws<Exception>(act);
        // "Failed to parse" in message
        Assert.Contains("Failed to parse", exception.Message);
    }

    [Fact]
    public void FromString_ShouldThrowExceptionWhenInvalidString()
    {
        // Arrange
        var planString = "Invalid string";

        // Act
        Action act = () => AIPlan.FromString(planString);

        // Assert
        var exception = Assert.Throws<Exception>(act);
        // "Failed to parse" in message
        Assert.Contains("Failed to parse", exception.Message);
    }

    [Fact]
    public void FromString_ShouldHaveEmptyDescriptionWhenNoDescription()
    {
        // Arrange
        var planString = "# AI Plan\n## Step 1: Operation1\n## Step 2: Operation2\n";
        var expectedOperations = new List<Operation>
        {
            new Operation("OPERATION1", ""),
            new Operation("OPERATION2", "")
        };

        // Act
        var aiPlan = AIPlan.FromString(planString);

        // Assert
        Assert.Equal(2, aiPlan.Operations.Count);
        Assert.Equal(expectedOperations[0].OperationName, aiPlan.Operations[0].OperationName);
        Assert.Equal(expectedOperations[0].Description, aiPlan.Operations[0].Description);
        Assert.Equal(expectedOperations[1].OperationName, aiPlan.Operations[1].OperationName);
        Assert.Equal(expectedOperations[1].Description, aiPlan.Operations[1].Description);
    }
}