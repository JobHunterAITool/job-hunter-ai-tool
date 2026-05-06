/**
 * App Component
 * 
 * Root component for the Job Hunter AI Tool frontend.
 * 
 * Author: Carl Ikai
 * Project: Job Hunter AI Tool
 */

import { useState } from "react";
import SearchForm from "./components/SearchForm";
import JobResults from "./components/JobResults";
import "./App.css";

function App() {
  /* Global application state shared by the search form and results panel */
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  return (
    <div>
      <h1>Job Hunter AI Tool</h1>

      {/* Two panel layout for search form and results */}
      <div className="two-panel-layout">
        {/* Search form panel */}
        <div>
          <SearchForm
            onResults={setResults}
            onLoadingChange={setIsLoading}
            onError={setError}
            onHasSearchedChange={setHasSearched}
            isLoading={isLoading}
          />
        </div>

        {/* Job results panel */}
        <div>
          <JobResults
            results={results}
            isLoading={isLoading}
            error={error}
            hasSearched={hasSearched}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
