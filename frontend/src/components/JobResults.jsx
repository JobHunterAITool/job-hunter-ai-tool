/**
 * JobResults Component
 * 
 * Displays the list of ranked job search results returned by
 * the backend API. 
 *
 * Author: Carl Ikai
 * Project: Job Hunter AI Tool
 */
function JobResults({ results = [], isLoading, error, hasSearched }) {
  const hasResults = results.length > 0;

  return (
    <div className="results-panel">
      <h2>Ranked Results</h2>

      {/* Display loading message while search request is processing */}
      {isLoading && (
        <div className="loading-state">
          <p>Searching for ranked job matches...</p>
        </div>
      )}

      {/* Display API error message if a request fails */}
      {!isLoading && error && <p className="error-message">{error}</p>}

      {/* Display first time message before the user submits a search */}
      {!isLoading && !error && !hasSearched && !hasResults && (
        <p className="results-empty">
          Submit a search to see ranked job matches.
        </p>
      )}

      {/* Display no results message after a completed search returns no jobs */}
      {!isLoading && !error && hasSearched && !hasResults && (
        <p className="results-empty">
          No matching jobs found. Try changing the title, location, or skills.
        </p>
      )}

      {/* Render list of job results */}
      {!isLoading &&
        !error &&
        hasResults &&
        results.map((job, index) => (
          <article
            key={`${job.title}-${job.company}-${index}`}
            className="result-card"
          >
            <h3>{job.title}</h3>

            <p>
              <strong>{job.company}</strong> | {job.location}
            </p>

            <p>Score: {Number(job.score).toFixed(2)}</p>

            <p>
              Matched skills: {(job.matched_skills ?? []).join(", ") || "None"}
            </p>
          </article>
        ))}
    </div>
  );
}

export default JobResults;
