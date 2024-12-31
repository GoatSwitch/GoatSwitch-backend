using Serilog.Core;
using Serilog.Events;
namespace API_Gateway.Services.Logging;

/// <summary>
/// Enriches log events with default properties.
/// If we dont do this, parsing via regex is harder.
/// </summary>
public class DefaultPropertyEnricher : ILogEventEnricher
{
    public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
    {
        logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("UserID", "NA"));
        logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("CompanyID", "NA"));
        logEvent.AddPropertyIfAbsent(propertyFactory.CreateProperty("TraceID", "NA"));
    }
}
