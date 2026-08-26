using AssessmentScoring.Services;
using Xunit;

namespace AssessmentScoring.Tests;

public class ScoringTests
{
    private readonly ScoringService _scorer = new();
    private static readonly List<AssessmentScoring.Models.AssessmentSection> Sections = ScoringFixtures.Sections;

    [Fact]
    [Trait("Category", "Scoring")]
    public void AllSectionsPass_ReturnsOverallPassed()
    {
        var answers = new Dictionary<string, string>
        {
            { "q1", "author" }, { "q2", "setting" }, { "q3", "plot" },
            { "q4", "main idea" }, { "q5", "inference" }, { "q6", "evidence" },
        };
        var result = _scorer.Calculate(answers, Sections);
        Assert.True(result.Passed);
        Assert.Equal(1.0, result.OverallPercentage, precision: 3);
        Assert.All(result.SectionScores, s => Assert.True(s.Passed));
    }

    [Fact]
    [Trait("Category", "Scoring")]
    public void FailedSection_FailsOverall_EvenIfWeightedAveragePasses()
    {
        // vocab: 0/3 = 0% (fails), comp: 3/3 = 100%
        var answers = new Dictionary<string, string>
        {
            { "q4", "main idea" }, { "q5", "inference" }, { "q6", "evidence" },
        };
        var result = _scorer.Calculate(answers, Sections);
        Assert.False(result.Passed);
        var vocab = result.SectionScores.Single(s => s.Id == "sec-vocab");
        Assert.False(vocab.Passed);
    }

    [Fact]
    [Trait("Category", "Scoring")]
    public void WeightedAverageBelowThreshold_FailsOverall()
    {
        // vocab: 3/3 = 100%, comp: 2/3 = 66.7% (fails)
        var answers = new Dictionary<string, string>
        {
            { "q1", "author" }, { "q2", "setting" }, { "q3", "plot" },
            { "q4", "main idea" }, { "q5", "inference" },
        };
        var result = _scorer.Calculate(answers, Sections);
        var comp = result.SectionScores.Single(s => s.Id == "sec-comp");
        Assert.False(comp.Passed);
        Assert.False(result.Passed);
    }

    [Fact]
    [Trait("Category", "Scoring")]
    public void WeightsAppliedCorrectly_ToOverallPercentage()
    {
        // vocab: 2/3, comp: 3/3 → (2/3)*0.4 + 1.0*0.6 = 0.867
        var answers = new Dictionary<string, string>
        {
            { "q1", "author" }, { "q2", "setting" },
            { "q4", "main idea" }, { "q5", "inference" }, { "q6", "evidence" },
        };
        var result = _scorer.Calculate(answers, Sections);
        Assert.Equal(0.867, result.OverallPercentage, precision: 3);
    }

    [Fact]
    [Trait("Category", "Scoring")]
    public void UnansweredQuestions_ScoreZeroInSection()
    {
        var answers = new Dictionary<string, string>
        {
            { "q4", "main idea" }, { "q5", "inference" }, { "q6", "evidence" },
        };
        var result = _scorer.Calculate(answers, Sections);
        var vocab = result.SectionScores.Single(s => s.Id == "sec-vocab");
        Assert.Equal(0, vocab.PointsEarned);
        Assert.Equal(3, vocab.PointsPossible);
    }

    [Fact]
    [Trait("Category", "Scoring")]
    public void EmptySubmission_ScoresZeroEverywhere()
    {
        var result = _scorer.Calculate(new Dictionary<string, string>(), Sections);
        Assert.Equal(0.0, result.OverallPercentage, precision: 3);
        Assert.False(result.Passed);
        Assert.All(result.SectionScores, s =>
        {
            Assert.Equal(0, s.PointsEarned);
            Assert.Equal(0.0, s.Percentage, precision: 3);
        });
    }
}
