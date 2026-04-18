export default function JobResults({ results, isLoading, error }) {
    return (
      <div className="results-panel">
        <h2>Ranked Results</h2>
  
        {isLoading && <p>Searching...</p>}
  
        {!isLoading && error ? (
          <p className="error-message">{error}</p>
        ) : null}
  
        {!isLoading && !error && results.length === 0 ? (
          <p className="results-empty">
            No results yet. Submit a search to query the backend.
          </p>
        ) : null}
  
        {!isLoading &&
          !error &&
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
                Matched skills:{" "}
                {(job.matched_skills ?? []).join(", ") || "None"}
              </p>
            </article>
          ))}
      </div>
    );
  }