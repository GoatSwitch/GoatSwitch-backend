using API_Gateway.Models.Authorization;
using Azure.Data.Tables;

namespace API_Gateway.Services;

public class AuthorizedUserService : IAuthorizedUserService
{
    private readonly ILogger<AuthorizedUserService> _logger;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly string _fakeAPIKey = "goatswitch_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";
    public static string DefaultUserID { get; private set; } = "DefaultUserID";
    public string UserID { get; private set; } = DefaultUserID;
    public string CompanyID { get; private set; } = "DefaultCompanyID";
    private readonly TableClient _usersTable;
    private readonly TableClient _apikeyTable;

    public AuthorizedUserService(IHttpClientFactory httpClientFactory, ILogger<AuthorizedUserService> logger)
    {
        this._logger = logger;
        this._httpClientFactory = httpClientFactory;

        var connectionString = Environment.GetEnvironmentVariable("AZ_TABLES_CONNECTION_STRING");
        var serviceClient = new TableServiceClient(connectionString);
        this._usersTable = serviceClient.GetTableClient("users");
        this._apikeyTable = serviceClient.GetTableClient("apikeys");
    }

    /// <summary>
    /// Get user email from GitHub API using the provided access token.
    /// </summary>
    /// <param name="accessToken"></param>
    /// <returns> Primary user email </returns>
    /// <exception cref="Exception"></exception>
    private async Task<string> GetUserEmailFromGitHub(string accessToken)
    {
        var request = new HttpRequestMessage(HttpMethod.Get, "https://api.github.com/user/emails");
        request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", accessToken);
        request.Headers.Add("User-Agent", "GoatSwitch-VSC"); // GitHub API requires a user-agent header

        var client = this._httpClientFactory.CreateClient();
        var response = await client.SendAsync(request);

        if (!response.IsSuccessStatusCode)
        {
            this._logger.LogError("GitHub API returned an error: {StatusCode}", response.StatusCode);
            this._logger.LogError("GitHub API returned an error: {ReasonPhrase}", response.ReasonPhrase);
            throw new Exception("Could not retrieve user email from GitHub.");
        }

        var json = await response.Content.ReadAsStringAsync();
        var emails =
            System.Text.Json.JsonSerializer.Deserialize<List<GitHubEmail>>(json)
            ?? throw new Exception("Could not retrieve user email from GitHub.");
        for (int i = 0; i < emails.Count; i++)
        {
            this._logger.LogDebug("   Email {i}: {Email}", i, emails[i].Email);
        }
        var primaryEmail = emails?.FirstOrDefault(e => e.Primary)?.Email;

        return primaryEmail ?? throw new Exception("Primary email not found.");
    }

    /// <summary>
    /// Get user email from Microsoft Graph API using the provided access token.
    /// </summary>
    /// <param name="accessToken"></param>
    /// <returns> User principal name </returns>
    /// <exception cref="Exception"></exception>
    private async Task<string> GetUserEmailFromMicrosoft(string accessToken)
    {
        var request = new HttpRequestMessage(HttpMethod.Get, "https://graph.microsoft.com/v1.0/me");
        request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", accessToken);
        var client = this._httpClientFactory.CreateClient();
        var response = await client.SendAsync(request);
        if (!response.IsSuccessStatusCode)
        {
            this._logger.LogError("Microsoft Graph API returned an error: {StatusCode}", response.StatusCode);
            this._logger.LogError("Microsoft Graph API returned an error: {ReasonPhrase}", response.ReasonPhrase);
            throw new Exception("Could not retrieve user email from Microsoft Graph.");
        }
        var json = await response.Content.ReadAsStringAsync();
        this._logger.LogDebug("Microsoft Graph API response: {json}", json);
        var graphResponse =
            System.Text.Json.JsonSerializer.Deserialize<MicrosoftGraphResponse>(json)
            ?? throw new Exception("Could not retrieve user email from Microsoft Graph.");
        return graphResponse.UserPrincipalName ?? throw new Exception("User principal name not found.");
    }

    /// <summary>
    /// Get user entity from azure table storage using the provided email.
    /// We di this to get the user ID and company ID for later logging.
    /// </summary>
    /// <param name="email"></param>
    /// <returns></returns>
    private async Task<TableEntity?> GetUserEntityAsync(string email)
    {
        await foreach (var entity in this._usersTable.QueryAsync<TableEntity>(filter: $"Email eq '{email}'"))
        {
            return entity;
        }
        return null;
    }
    private async Task<TableEntity?> GetAPIKeyEntityAsync(string apiKey)
    {
        // clean benchmark run name appended to the api key
        var apiKeyClean = apiKey.Substring(0, this._fakeAPIKey.Length);
        await foreach (var entity in this._apikeyTable.QueryAsync<TableEntity>(filter: $"RowKey eq '{apiKeyClean}'"))
        {
            return entity;
        }
        return null;
    }
    void SetUserInformationfromTable(TableEntity entity)
    {
        this.UserID = entity.RowKey;
        this.CompanyID = entity.PartitionKey;
        this._logger.LogInformation("User found, UserID: {userID}, CompanyID: {companyID}",
          entity.RowKey, entity.PartitionKey);
    }
    /// <summary>
    /// Set user information from the API key.
    /// The api key might be just len(_demoAPIKey) characters long, then we know it's just a development request.
    /// If it's longer it's a benchmark run and concatenated to it is the run-id
    /// Example dev: "goatswitch_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" or 
    /// Example bench: "goatswitch_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx00001"
    /// </summary>
    /// <param name="apiKey"></param>
    void SetUserInformationfromAPIKey(TableEntity entity, string apiKey)
    {
        // check if it's a named benchmark run or just a development request
        if (apiKey.Length > this._fakeAPIKey.Length)
        {
            this.UserID = apiKey.Substring(this._fakeAPIKey.Length);
            this.CompanyID = entity.PartitionKey;
            this._logger.LogInformation("Benchmark API key detected");
        }
        else
        {
            // don't set user id; leave it as default; will later be overwritten by connection id
            this.CompanyID = entity.PartitionKey;
            this._logger.LogInformation("Demo API key detected");
        }
    }

    private async Task<Boolean> IsUserEntityAuthorized(TableEntity entity)
    {
        // TODO: Handle if we have users not alowed to use the API for some reason
        return true;
    }
    /// <summary>
    /// Check if the user is authorized based on the provided access token.
    /// </summary>
    /// <param name="accessToken"></param>
    /// <returns> True if the user is authorized, false otherwise </returns>
    public async Task<bool> IsAuthorized(string accessToken)
    {
        if (accessToken.StartsWith("goatswitch_"))
        {
            this._logger.LogInformation("GoatSwitch AI API key detected");
            var apiKeyEntity = await GetAPIKeyEntityAsync(accessToken);
            if (apiKeyEntity != null)
            {
                this.SetUserInformationfromAPIKey(apiKeyEntity, accessToken);
                return true;
            }
            else
            {
                this._logger.LogInformation("GoatSwitch AI API key not valid");
                return false;
            }
        }
        string email;
        // determine if token is github or microsoft
        if (accessToken.StartsWith("ghp_") || accessToken.StartsWith("gho_"))
        {
            this._logger.LogInformation("GitHub token detected");
            email = await GetUserEmailFromGitHub(accessToken);
        }
        else
        {
            this._logger.LogInformation("Microsoft token detected");
            email = await GetUserEmailFromMicrosoft(accessToken);
        }
        this._logger.LogInformation("User email: {email}", email);
        bool isAuth = false;
        var userEntity = await GetUserEntityAsync(email);
        if (userEntity != null)
        {
            this.SetUserInformationfromTable(userEntity);
            isAuth = await IsUserEntityAuthorized(userEntity);
        }
        return isAuth;
    }
}
