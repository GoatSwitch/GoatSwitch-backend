using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace API_Gateway.Models.Authorization;

public class GitHubEmail
{
    [JsonPropertyName("email")]
    public string? Email { get; set; }

    [JsonPropertyName("primary")]
    public bool Primary { get; set; }

    [JsonPropertyName("verified")]
    public bool Verified { get; set; }

    [JsonPropertyName("visibility")]
    public string? Visibility { get; set; }
}

public class GitHubEmailResponse
{
    public List<GitHubEmail>? Emails { get; set; }
}
