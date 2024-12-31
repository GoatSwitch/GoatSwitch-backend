namespace API_Gateway.Services;

public interface IAuthorizedUserService
{
    public string UserID { get; }
    public string CompanyID { get; }
    Task<bool> IsAuthorized(string accessToken);
}
