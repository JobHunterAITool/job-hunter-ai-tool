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
  /* Local component state for form inputs */
  const [jobTitle, setJobTitle] = useState("");
  const [skills, setSkills] = useState("");
  const [location, setLocation] = useState("");
  const [experience, setExperience] = useState("");

  /**
   * Handle form submission.
   */
  async function handleSubmit(e) {
    e.preventDefault();

    /* Reset stale UI state before starting a new request */
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

        {/* Job title input */}
        <input
          placeholder="Job Title"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
          disabled={isLoading}
          required
        />

        {/* Skills input */}
        <input
          placeholder="Skills (comma separated)"
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
          disabled={isLoading}
          required
        />

        {/* Location input */}
        <input
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          disabled={isLoading}
          required
        />

        {/* Years of experience typed input */}
        <input
          type="number"
          placeholder="Years of Experience"
          value={experience}
          onChange={(e) => setExperience(e.target.value)}
          disabled={isLoading}
          min="0"
          required
        />

        {/* Submit button */}
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Searching..." : "Search Jobs"}
        </button>
      </form>

      <ResumeUpload
        onResults={onResults}
        onLoadingChange={onLoadingChange}
        onError={onError}
        onHasSearchedChange={onHasSearchedChange}
      />
    </div>
  );
}
