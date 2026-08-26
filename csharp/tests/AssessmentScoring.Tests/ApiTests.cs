using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Xunit;

namespace AssessmentScoring.Tests;

public class ApiTests : IClassFixture<TestWebAppFactory>
{
    private readonly HttpClient _client;

    public ApiTests(TestWebAppFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task Submit_MissingStudentId_Returns422()
    {
        var response = await _client.PostAsJsonAsync(
            "/assessments/assess-001/submit",
            new { answers = new Dictionary<string, string> { { "q-001", "author" } } });
        Assert.Equal(HttpStatusCode.UnprocessableEntity, response.StatusCode);
    }

    [Fact]
    public async Task Submit_UnknownAssessment_Returns404()
    {
        var response = await _client.PostAsJsonAsync(
            "/assessments/does-not-exist/submit",
            new { student_id = "student-1", answers = new Dictionary<string, string>() });
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task Submit_Returns500_BeforeScoringImplemented()
    {
        var response = await _client.PostAsJsonAsync(
            "/assessments/assess-001/submit",
            new { student_id = "student-001", answers = new Dictionary<string, string> { { "q-001", "author" } } });
        Assert.Equal(HttpStatusCode.InternalServerError, response.StatusCode);
    }

    [Fact]
    public async Task GetScores_NewStudent_ReturnsEmptyList()
    {
        var response = await _client.GetAsync("/students/brand-new-student/scores");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var results = await response.Content.ReadFromJsonAsync<List<object>>();
        Assert.NotNull(results);
        Assert.Empty(results);
    }

    [Fact]
    public async Task GetClasses_ReturnsList()
    {
        var response = await _client.GetAsync("/classes");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var data = await response.Content.ReadFromJsonAsync<List<JsonElement>>();
        Assert.NotNull(data);
        Assert.Equal(3, data.Count);
    }

    [Fact]
    public async Task GetClass_ReturnsStudentsWithoutScores()
    {
        var response = await _client.GetAsync("/classes/class-001");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var data = await response.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal("class-001", data.GetProperty("id").GetString());
        Assert.Equal("Room 12A", data.GetProperty("name").GetString());
        Assert.Equal("Ms. Rivera", data.GetProperty("teacher_name").GetString());
        Assert.Equal(5, data.GetProperty("students").GetArrayLength());
        Assert.False(data.TryGetProperty("scores", out _));
        Assert.False(data.TryGetProperty("submissions", out _));
    }

    [Fact]
    public async Task GetClass_Returns404ForUnknownClass()
    {
        var response = await _client.GetAsync("/classes/does-not-exist");
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task GetAssessments_ReturnsList()
    {
        var response = await _client.GetAsync("/assessments");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var data = await response.Content.ReadFromJsonAsync<List<JsonElement>>();
        Assert.NotNull(data);
        Assert.Equal(2, data.Count);
    }

    [Fact]
    public async Task Submit_ReturnsScoreResult()
    {
        var response = await _client.PostAsJsonAsync(
            "/assessments/assess-001/submit",
            new
            {
                student_id = "student-abc",
                answers = new Dictionary<string, string>
                {
                    { "q-001", "author" }, { "q-002", "setting" }, { "q-003", "plot" },
                    { "q-004", "main idea" }, { "q-005", "inference" },
                },
            });
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var data = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
        Assert.NotNull(data);
        Assert.True(data.ContainsKey("submission_id"));
        Assert.True(data.ContainsKey("overall_percentage"));
        Assert.True(data.ContainsKey("section_scores"));
    }

    [Fact]
    public async Task GetScores_AfterSubmit_ReturnsSubmission()
    {
        await _client.PostAsJsonAsync(
            "/assessments/assess-002/submit",
            new
            {
                student_id = "student-xyz",
                answers = new Dictionary<string, string> { { "q-008", "12" } },
            });

        var response = await _client.GetAsync("/students/student-xyz/scores");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var results = await response.Content.ReadFromJsonAsync<List<object>>();
        Assert.NotNull(results);
        Assert.Single(results);
    }
}
