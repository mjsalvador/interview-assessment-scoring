using AssessmentScoring.Models;

namespace AssessmentScoring.Services;

public class ScoringService
{
    /// <summary>
    /// Score a student's submitted answers across a sectioned assessment.
    ///
    /// Each section has a weight and its own set of questions. The student must
    /// meet the mastery threshold both overall (weighted) and in each section
    /// individually to pass.
    /// </summary>
    /// <param name="submittedAnswers">Maps question ID to the student's answer string.</param>
    /// <param name="sections">
    ///   List of sections, each with Id, Name, Weight, and Questions (dict of questionId to correctAnswer).
    /// </param>
    /// <returns>
    ///   ScoreResult containing per-section scores, overall weighted percentage, and passed flag.
    ///   Passed is true only if overall_percentage >= MasteryThreshold AND every section passed.
    /// </returns>
    /// <remarks>
    /// Rules:
    ///   - Unanswered questions count as incorrect
    ///   - Extra answers not in any section are ignored
    ///   - Comparison is case-insensitive
    ///   - An empty submission is valid and scores 0
    ///   - Section weights are guaranteed to sum to 1.0
    ///
    /// TODO: Implement this method.
    /// The tests in ScoringTests.cs define the expected behavior.
    /// Run: docker compose run test --filter "Category=Scoring"
    /// </remarks>
    public ScoreResult Calculate(
        Dictionary<string, string> submittedAnswers,
        List<AssessmentSection> sections)
    {
        throw new NotImplementedException();
    }
}
