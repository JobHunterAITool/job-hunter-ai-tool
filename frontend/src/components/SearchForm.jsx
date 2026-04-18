import { useState } from "react";
import { searchJobs } from "../api";

export default function SearchForm() {
  const [jobTitle, setJobTitle] = useState("");
  const [skills, setSkills] = useState("");
  const [location, setLocation] = useState("");
  const [experience, setExperience] = useState("Mid");
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    const payload = {
      job_title: jobTitle,
      skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
      location,
      experience_level: experience,
    };

    try {
      const response = await searchJobs(payload);
      setResults(response.results ?? []);
    } catch (requestError) {
      setResults([]);
      setError(requestError.message || "Search failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="search-section">
      <form onSubmit={handleSubmit}>
        <h2>Job Search</h2>

        <input
          placeholder="Job Title"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
          required
        />

        <input
          placeholder="Skills (comma separated)"
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
          required
        />

        <input
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          required
        />

        <select
          value={experience}
          onChange={(e) => setExperience(e.target.value)}
          required
        >
          <option value="Entry">Entry</option>
          <option value="Mid">Mid</option>
          <option value="Senior">Senior</option>
        </select>

        <button type="submit" disabled={isLoading}>
          {isLoading ? "Searching..." : "Search Jobs"}
        </button>
      </form>

      {error ? <p className="error-message">{error}</p> : null}

      <div className="results">
        <h3>Ranked Results</h3>
        {!isLoading && results.length === 0 ? (
          <p className="results-empty">No results yet. Submit a search to query the backend.</p>
        ) : null}
        {results.map((job, index) => (
          <article key={`${job.title}-${job.company}-${index}`} className="result-card">
            <h4>{job.title}</h4>
            <p>{job.company} | {job.location}</p>
            <p>Score: {Number(job.score).toFixed(2)}</p>
            <p>Matched skills: {(job.matched_skills ?? []).join(", ") || "None"}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
