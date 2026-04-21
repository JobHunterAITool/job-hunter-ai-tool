/**
 * JobResults Component
 * 
 * Displays the list of ranked job search results returned by
 * the backend or mock API. Handles loading states, error
 * messages, and empty result sets.
 *
 * Author: Carl Ikai
 * Project: Job Hunter AI Tool
 */
function JobResults({ results = [], isLoading, error }) {
    return (
      <div className="results-panel">
        <h2>Ranked Results</h2>
  
        {/* Display loading message while search request is processing */}
        {isLoading && <p>Searching...</p>}
  
        {/* Display API error message if a request fails */}
        {!isLoading && error && (
          <p className="error-message">{error}</p>
        )}
  
        {/* Display message when no results are returned */}
        {!isLoading && !error && results.length === 0 && (
          <p className="results-empty">
            No results yet. Submit a search to query the backend.
          </p>
        )}
  
        {/* Render list of job results */}
        {!isLoading &&
          !error &&
          results.map((job, index) => (
            <article
              key={`${job.company}-${index}`}
              className="result-card"
            >
              {/* Display company name for each job result */}
              <p>{job.company}</p>
            </article>
          ))}
      </div>
    );
  }
  
  export default JobResults;