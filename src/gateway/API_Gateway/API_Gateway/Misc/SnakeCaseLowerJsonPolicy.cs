using System.Text.Json;

namespace API_Gateway.Misc;

public class SnakeCaseJsonNamingPolicy : JsonNamingPolicy
{
    public override string ConvertName(string name)
    {
        // Convert camelCase to snake_case
        return string.Concat(name.Select((x, i) => i > 0 && char.IsUpper(x) ? "_" + x.ToString() : x.ToString()))
            .ToLower();
    }
}
