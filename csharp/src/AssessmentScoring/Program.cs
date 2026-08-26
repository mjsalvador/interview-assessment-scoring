using System.Text.Json;
using AssessmentScoring.Controllers;
using AssessmentScoring.Data;
using AssessmentScoring.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
    options.SerializerOptions.PropertyNameCaseInsensitive = true;
});

var dbPath = builder.Configuration["DbPath"] ?? Path.Combine(AppContext.BaseDirectory, "assessments.db");
var connectionString = $"Data Source={dbPath}";

builder.Services.AddSingleton(new Database(connectionString));
builder.Services.AddSingleton<ScoringService>();

var app = builder.Build();

app.Services.GetRequiredService<Database>().InitDb();

AssessmentController.MapRoutes(app);

app.Run();

public partial class Program { }
