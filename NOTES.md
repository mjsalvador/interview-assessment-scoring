# Notes

## How the service works
<!-- Describe the end-to-end flow in your own words: what happens from HTTP request to stored result -->
The three resources exposed by this API are `assessments`, `students`, and `classes`. `app.py` instantiates a FastAPI service and manages routing and error-handling by matching incoming requests' methods and paths to an associated route handler. Each database function opens and closes its own connection and Pydantic models are used to validate incoming request bodies and define response shapes.

The existing GET endpoints are fairly trivial. `GET /students/{student_id}/scores` returns stored submissions for a student. `GET /classes` returns a list of classes and `GET /classes/{class_id}` returns a class's details joined with its student roster. `GET /assessments` and `GET /assessments/{assessment_id}` returns a list of assessments or a single assessment.

An assessment submission comes in as `POST /assessments/{assessment_id}/submit` with a student's answers to an assessment, and its handler loads the assessment, its sections, and the answer key, raising a 404 if the assessment does not exist. The student's submission is then used by `calculate_score` to compare against each section's answer key and calculate the student's section scores, which are returned along with a weighted overall percentage, and a pass flag. The grades and submission are finally stored in the `submissions` table and returned to the user.

## Scoring function
<!-- How did you approach implementing calculate_score? Any edge cases that gave you pause? -->
`calculate_score` iterates through each section's questions rather than a student's submitted answers. I originally thought to iterate through the student's submitted answers but decided against it because of the first two rules. By anchoring the sections, the first two rules were handled for free: a question with no answer counts as incorrect, and an answer to a question that doesn't belong to any section is ignored. Within a section, it counts the correct answers, computes the section percentage, decides whether that section met the mastery threshold, and adds the section's weighted contribution to a running overall total. After every section is scored, it decides the overall results based on if the weighted total meets or exceeds the threshold and every section was passed.

There were a few edge cases that I had to think through:

1. A section with no questions would divide by zero [divide by zero](./python/src/scoring.py#L61) and trying to amend this would've been a guess. Scoring it 1.0 hands out free points weighted into the overall score, but 0.0 makes the assessment impossible to pass, and dropping it rewrites the assessment's section's weights. I decided to flag an empty section as invalid rather than hiding it behind a plausible number because an assessment with an empty section is a signal of its misconfiguration.

2. Floating-point arithmetic can fail a student who scored exactly 80%. In the case where a student scored 4/5 on an assessment's two sections that are weighted 0.7 and 0.3, each section passes the threshold mastery, but the weighted sum evaluates to 0.7999999999999999 so a raw comparison counts that as an overall failure. The [overall pass check](./python/src/scoring.py#L75) rounds the weighted overall total to 9 decimal places before comparing it to the threshold value, which discards floating-point errors without meaningfully altering the score. If overall weighted totals were rounded to 2 decimal places, a 0.795 would register a section as passing. Rounding the [overall percentage](./python/src/scoring.py#L80) to 4 decimal places after `passed` is already decided can't change anyone's result and was used to deliver a cleaner payload.

3. Answer-matching is case-insensitive per the rules using `casefold`, and also trims leading and trailing spaces while preserving internal spaces. Special and international alphabets are left alone because whether "café" and "cafe" match changes what counts as correct and is a question for the product team to explicitly handle.


## Class results feature
<!-- What did you build? Why did you structure it the way you did?
     If you chose to extend an existing endpoint vs. create a new one, explain that choice. -->
I created a new endpoint `GET /classes/{class_id}/results` with an optional `assessment_id` query parameter that returns a class and a roster of its students with their submissions, and a per-assessment summary that includes per-section performance.

Extending `GET /classes/{class_id}` was the other option but was ultimately decided against for two reasons:

1. The tests asserted that the response doesn't include score or submission data, so extending the endpoint meant having to edit a test that exists to protect an existing contract, and consumers would start paying for data they might not necessarily need. 

2. Following RESTful conventions, a class resource should describe the class and who is in it but introducing assessment results to the class resource conflates a class's identity with its performance. 

I decided that an assessment can be specified in the query string to allow the flexibility of understanding how a class did on a specific assessment, and how a class is doing across assessments, which can be useful for identifying trends and progress. 

A student's assessment submission and their section scores and overall result all come from a single query joining the class's students and their submissions. I considered querying in steps, first querying for students and then querying submissions for each student, but that would have introduced the N+1 query problem that would result in performance bottlenecks as class sizes and assessments scale.

A single pass over the rows is done to build the `students` and `assessments` dicts. For each row, the student is added to `students` and only then checks a student's submission. If a student doesn't have a submission, they are still included in the list with empty submissions rather than being dropped. `section_scores` and submission data are parsed into a `SubmissionResponse` and appended to the student's submissions, and the assessments are added to `assessments`.

Each student's section scores are accumulated per section of that assessment: their score is added to a list to be averaged, and the student is sorted into passing or failing buckets.

The assessment summary is then computed from each assessment, per section: the class average, how many students submitted, how many students passed, which students passed, and which students failed.

Averages and pass counts only cover students who submitted because a student not taking an assessment is not reflective of their understanding of the material, so averaging them as a zero would inaccurately portray overall class understanding, and dropping them would hide that they are missing, so the inclusion of `students_not_submitted_ids` immediately surfaces which students did not submit their assessment.

## Tradeoffs and what I'd do next
<!-- What tradeoffs did you make? What would you tackle with more time? -->
Some tradeoffs I made were:

- Creating a new endpoint to surface class results instead of extending the existing endpoint: teachers now have to make two requests and the API has one more route to maintain but I was able to preserve the existing contract defined by the tests, and the class resource keeps its meaning.

- Assessment as a query parameter: the response shape varies with each request and we now need to handle both cases but we can use one endpoint to answer two questions a teacher asks: how did the class do on this assessment, and how has the class been doing over the past few assessments?

- Class averages not reflecting the entire class size can look misleading in the rare case of a meaningful amount of students missing an assessment, but an absent student doesn't affect the perceived performance of the class. Including a list of students who did not submit assessments provides more insight.

- Raising an error if a section has no questions means a failed submission for a student who did nothing wrong but surfaces misconfigured assessments.

If I had more time, some things I would do are:

- I followed the existing code architecture to stay consistent rather than introduce a brand new convention in a codebase that could break tests. If the product continued to scale, I would modularize the service: a data-access layer would be limited to queries, a service layer would hold business logic and assemble responses, and a dedicated routing layer would handle the requests. I would also colocate each resource (router, service, data-access, models) under its own directory rather than grouping by file type.

- Submissions have no history or timestamps because saving overwrites a student's previous result for the same assessment, so there is no way to show growth over time so I would add timestamps to submission history as well as a unique constraint to the submissions table.

- There is no relationship between classes and assessments so "this assessment was never given to this class" and "this assessment was given to this class but nobody has submitted" would have the same results even though they describe two different scenarios. A new `class_assessments` table would tell a teacher which assessments are available for a class, instead of querying them to know an assessment ID in advance.


## Working with AI
<!-- How did you use AI tools? What did you prompt, what came back, what did you change and why?
     Think of this as a reflection on the collaboration, not a log. -->
I used Claude to help plan and implement the solution. I mostly use Claude as a rubber ducky during coding sessions to bounce ideas off of but when it comes to an entire end to end workflow, it usually looks like prompting it to:

1. Perform an analysis of the codebase and generate a report documenting, most importantly, an executive summary, the code and system architecture, any API endpoints with an example request traced end-to-end, and the key components of the system. The generated report for this codebase can be seen in [CODEBASE_REPORT.md](./CODEBASE_REPORT.md).

2. Plan the implementation of required features but with me driving the conversation. I would always explain my own approach and assumptions first and then have Claude plan around that. I never let Claude plan anything by itself, using it mostly to identify holes and gaps in my proposed plans. The generated plan can be seen in [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md).

3. Once I explicitly confirmed the plans would I finally let Claude generate any code. I mostly write the code myself but in this exercise I let Claude generate everything. Once the code was implemented, I would read through it line-by-line to make sure I understood everything it wrote and it followed the plan. If there was something that didn't make sense to me then I'd probe Claude about it and see if there's a better way to write it that was easier to reason about. 

I found explicitly stating myself as the primary driver of the conversation and planning results in more of myself ending up in the final code, and maintained alignment every step of the way, which means less pushing or pulling. In my global CLAUDE.md file, I also explicitly state to never blindly agree with what I'm saying and to challenge my thinking so I can be confident that the decided-on plan was well vetted.

In this exercise specifically, one thing I came back to was `AssessmentResultsSummary`. Originally Claude had scoped the model with only the number of students who had not submitted an assessment, but I thought it would be more useful to also include a list of those students so I prompted Claude for an amendment and it agreed with it. 