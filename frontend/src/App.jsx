import { useState } from "react";
import SearchForm from "./components/SearchForm";
import JobResults from "./components/JobResults";
import "./App.css";

function App() {
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  return (
    <div>
      <h1>Job Hunter AI Tool</h1>

      <div className="two-panel-layout">
        <div>
          <SearchForm
            onResults={setResults}
            onLoadingChange={setIsLoading}
            onError={setError}
            isLoading={isLoading}
          />
        </div>

        <div>
          <JobResults
            results={results}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </div>
    </div>
  );
}

export default App;