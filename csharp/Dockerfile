FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /app
COPY AssessmentScoring.sln .
COPY src/AssessmentScoring/AssessmentScoring.csproj src/AssessmentScoring/
COPY tests/AssessmentScoring.Tests/AssessmentScoring.Tests.csproj tests/AssessmentScoring.Tests/
RUN dotnet restore
COPY . .
RUN dotnet publish src/AssessmentScoring -c Release -o /out

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /out .
ENTRYPOINT ["dotnet", "AssessmentScoring.dll"]
