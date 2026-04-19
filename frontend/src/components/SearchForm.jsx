import { useState } from "react";
import { mockSearchJobs } from "../services/mockAPI";

export default function SearchForm({
  onResults,
  onLoadingChange,
  onError,
  isLoading,
}) {
  const [jobTitle, setJobTitle] = useState("");
  const [skills, setSkills] = useState("");
  const [location, setLocation] = useState("");
  const [experience, setExperience] = useState("Mid");

  async function handleSubmit(e) {
    e.preventDefault();
    onError("");
    onLoadingChange(true);

    const payload = {
      job_title: jobTitle,
      skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
      location,
      experience_level: experience,
    };

    try {
      const response = await mockSearchJobs(payload);
      onResults(response);
    } catch (requestError) {
      onResults([]);
      onError(requestError.message || "Search failed.");
    } finally {
      onLoadingChange(false);
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
    </div>
  );
}