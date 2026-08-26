using AssessmentScoring.Data;
using AssessmentScoring.Models;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;

namespace AssessmentScoring.Tests;

public class TestWebAppFactory : WebApplicationFactory<Program>
{
    private readonly string _dbPath;

    public TestWebAppFactory()
    {
        _dbPath = Path.Combine(Path.GetTempPath(), $"test_{Guid.NewGuid():N}.db");
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseSetting("DbPath", _dbPath);
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);
        if (disposing && File.Exists(_dbPath))
            File.Delete(_dbPath);
    }
}

public static class ScoringFixtures
{
    public static readonly List<AssessmentSection> Sections = new()
    {
        new AssessmentSection(
            Id: "sec-vocab",
            Name: "Vocabulary",
            Weight: 0.4,
            Questions: new Dictionary<string, string>
            {
                { "q1", "author" },
                { "q2", "setting" },
                { "q3", "plot" },
            }),
        new AssessmentSection(
            Id: "sec-comp",
            Name: "Comprehension",
            Weight: 0.6,
            Questions: new Dictionary<string, string>
            {
                { "q4", "main idea" },
                { "q5", "inference" },
                { "q6", "evidence" },
            }),
    };
}
