using System.Text.RegularExpressions;
using Serilog.Core;
using Serilog.Events;

namespace API_Gateway.Services.Logging;

/// <summary>
/// Enriches log events with redacted access tokens.
/// Otherwise authentication tokens would be logged in plain text.
/// </summary>
public class AccessTokenEnricher : ILogEventEnricher
{
    private static readonly Regex AccessTokenRegex = new Regex(@"access_token=[^&\s]+", RegexOptions.Compiled);

    public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
    {
        if (logEvent.Properties["QueryString"] != null)
        {
            if (AccessTokenRegex.IsMatch(logEvent.Properties["QueryString"].ToString()))
            {
                var redactedString = AccessTokenRegex.Replace(logEvent.Properties["QueryString"].ToString(), "access_token=[REDACTED]");
                logEvent.AddOrUpdateProperty(propertyFactory.CreateProperty("QueryString", redactedString));
            }
        }
        for (int i = 0; i < logEvent.Properties.Count; i++)
        {
            var key = logEvent.Properties.Keys.ElementAt(i);
            if (key == "HostingRequestFinishedLog" || key == "HostingRequestStartingLog")
            {
                var property = logEvent.Properties.Values.ElementAt(i).ToString();
                if (AccessTokenRegex.IsMatch(property))
                {
                    var redactedString = AccessTokenRegex.Replace(property, "access_token=[REDACTED]");
                    logEvent.AddOrUpdateProperty(propertyFactory.CreateProperty(key, redactedString));
                }
            }
        }
    }
}
