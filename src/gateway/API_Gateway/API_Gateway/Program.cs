using System.Diagnostics;
using System.Globalization;
using System.Reflection;
using API_Gateway.Hubs;
using API_Gateway.Misc;
using API_Gateway.Services;
using API_Gateway.Services.Logging;
using Dapr.Client;
using Grpc.Net.Client;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Extensions.FileProviders;
using OpenTelemetry.Exporter;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using Serilog;

var cultureInfo = new CultureInfo("en-US");
CultureInfo.DefaultThreadCurrentCulture = cultureInfo;
CultureInfo.DefaultThreadCurrentUICulture = cultureInfo;

var builder = WebApplication.CreateBuilder(args);

Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.With(new AccessTokenEnricher(), new DefaultPropertyEnricher())
    .CreateLogger();

builder.Logging.ClearProviders();
builder.Logging.AddSerilog(Log.Logger);

builder
    .Services.AddOpenTelemetry()
    .ConfigureResource(resource => resource.AddService(serviceName: "GoatSwitchAI-API"))
    .WithTracing(t_builder =>
    {
        // add the Workflow activity sources so they are traced
        t_builder
            .AddSource("WorkflowMigrate")
            .AddSource("WorkflowGenPlan")
            .AddSource("WorkflowExecutePlan")
            .AddSource("WorkflowGenerateTests")
            .AddSource("WorkflowRetry")
            .AddSource("WorkflowImprove")
            .SetSampler(new AlwaysOnSampler());
        var tracingExporter = builder
            .Configuration.GetValue("Tracing:UseTracingExporter", defaultValue: "console")!
            .ToLowerInvariant();
        switch (tracingExporter)
        {
            case "otlp":
                t_builder.AddOtlpExporter();
                t_builder.ConfigureServices(services =>
                {
                    services.Configure<OtlpExporterOptions>(builder.Configuration.GetSection("Tracing:Otlp"));
                });
                break;

            default:
                t_builder.AddConsoleExporter();
                break;
        }
    });

// Add services to the container.
builder.Services.AddTransient<IUTPickerCallerService, UTPickerCallerService>();
builder.Services.AddTransient<IUTGeneratorCallerService, UTGeneratorCallerService>();
builder.Services.AddTransient<ITLGeneratorCallerService, TLGeneratorCallerService>();
builder.Services.AddTransient<ITLPickerCallerService, TLPickerCallerService>();
builder.Services.AddTransient<IPlanGeneratorCallerService, PlanGeneratorCallerService>();
builder.Services.AddTransient<ISignalRLogService, SignalRLogService>();
builder.Services.AddTransient<IAuthorizedUserService, AuthorizedUserService>();
builder.Services.AddTransient<IBackupService, BackupService>();
builder.Services.AddDaprClient(cl =>
    cl.UseGrpcChannelOptions(
        new GrpcChannelOptions
        {
            MaxReceiveMessageSize = 128 * 1024 * 1024, // 128 MB
            MaxSendMessageSize = 128 * 1024 * 1024 // 128 MB
        }
    )
);

builder
    .Services.AddSignalR(hubOptions =>
    {
        hubOptions.MaximumReceiveMessageSize = 128 * 1024 * 1024; // 128 MB
    })
    .AddJsonProtocol(options =>
    {
        options.PayloadSerializerOptions.PropertyNamingPolicy = new SnakeCaseJsonNamingPolicy();
    });

builder.Services.AddControllers().AddDapr();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddHttpClient();

var app = builder.Build();
DistributedContextPropagator.Current = DistributedContextPropagator.CreatePassThroughPropagator();

IncreaseDaprTimeout(app, TimeSpan.FromSeconds(1000));

// Configure the HTTP request pipeline.
// Add Swagger documentation only to development builds
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors(builder =>
{
    // Disable cors completely so also external resources are able to call this api
    builder.AllowAnyHeader().AllowAnyMethod().AllowCredentials().SetIsOriginAllowed(_ => true);
});

app.UseRouting();
app.UseAuthentication();
app.UseDefaultFiles();
app.MapControllers(); //.RequireAuthorization();

app.MapHub<FrontendHub>("/frontendhub");

Log.Information("Starting application...");
app.Run();

/// <summary>
/// Increases timeout of dapr internal http client with use of reflection.
/// This is because dapr SDK does not offer any smooth way to set this.
/// If there is any way to configure this setting over the dapr SDK officially in the future this method should be replaced
/// </summary>
/// <param name="app">Web application of ASP.Net</param>
/// <param name="timeout">Timeout after the dapr request should be cancelled</param>
void IncreaseDaprTimeout(WebApplication app, TimeSpan timeout)
{
    DaprClient daprClient = app.Services.GetRequiredService<DaprClient>();

    FieldInfo[] fields = daprClient.GetType().GetFields(BindingFlags.NonPublic | BindingFlags.Instance);
    FieldInfo? httpClientField = fields.FirstOrDefault(x => x.Name == "httpClient");

    ArgumentNullException.ThrowIfNull(httpClientField);

    HttpClient? httpClient = httpClientField.GetValue(daprClient) as HttpClient;

    ArgumentNullException.ThrowIfNull(httpClient);

    httpClient.Timeout = timeout;
}
