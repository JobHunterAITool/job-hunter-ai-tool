/**
 * SearchForm Component
 *
 * Provides the job search form UI for the Job Hunter AI Tool.
 * Collects user input and sends the search request to the backend.
 *
 * Author: Carl Ikai
 * Project: Job Hunter AI Tool
 */

import { useState } from "react";
import { searchJobs } from "../services/api";
import ResumeUpload from "./ResumeUpload";

export default function SearchForm({
  onResults,
  onLoadingChange,
  onError,
  onHasSearchedChange,
  isLoading,
}) {
  const [jobTitle, setJobTitle] = useState("");
  const [skills, setSkills] = useState("");
  const [location, setLocation] = useState("");
  const [experience, setExperience] = useState("");
  const [resumeResetKey, setResumeResetKey] = useState(0);

  /**
   * Clear manual search inputs after resume upload.
   */
  function clearSearchFields() {
    setJobTitle("");
    setSkills("");
    setLocation("");
    setExperience("");
  }

  async function handleSubmit(e) {
    e.preventDefault();

    /* Clear resume preview after manual search */
    setResumeResetKey((prev) => prev + 1);

    onResults([]);
    onError("");
    onHasSearchedChange(true);
    onLoadingChange(true);

    const payload = {
      job_title: jobTitle,
      skills: skills
        .split(",")
        .map((skill) => skill.trim())
        .filter(Boolean),
      location,
      experience_level: Number.parseInt(experience, 10),
    };

    try {
      const response = await searchJobs(payload);

      const searchResults = Array.isArray(response)
        ? response
        : response.results || [];

      onResults(searchResults);
    } catch (requestError) {
      onResults([]);
      onError(
        requestError.message ||
          "We could not complete the search. Please try again."
      );
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
          disabled={isLoading}
          required
        />

        <input
          placeholder="Skills (comma separated)"
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
          disabled={isLoading}
          required
        />

        <input
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          disabled={isLoading}
          required
        />

        <input
          type="number"
          placeholder="Years of Experience"
          value={experience}
          onChange={(e) => setExperience(e.target.value)}
          disabled={isLoading}
          min="0"
          required
        />

        <button type="submit" disabled={isLoading}>
          {isLoading ? "Searching..." : "Search Jobs"}
        </button>
      </form>

      <ResumeUpload
        resetKey={resumeResetKey}
        onClearSearchFields={clearSearchFields}
        onResults={onResults}
        onLoadingChange={onLoadingChange}
        onError={onError}
        onHasSearchedChange={onHasSearchedChange}
      />
    </div>
  );
}