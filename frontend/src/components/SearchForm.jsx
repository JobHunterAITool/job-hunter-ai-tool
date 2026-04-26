/**
 * SearchForm Component
 * 
 * Provides the job search form UI for the Job Hunter AI Tool.
 * Collects user input and sends the search request to the
 * backend.
 *
 * Author: Carl Ikai
 * Project: Job Hunter AI Tool
 */

import { useState } from "react";
import { mockSearchJobs } from "../services/mockAPI";

export default function SearchForm({
  onResults,
  onLoadingChange,
  onError,
  isLoading,
}) {

  /* Local component state for form inputs */
  const [jobTitle, setJobTitle] = useState("");
  const [skills, setSkills] = useState("");
  const [location, setLocation] = useState("");
  const [experience, setExperience] = useState("Mid");

  /**
   * Handle form submission.
   *
   * Builds the search payload from form inputs and sends
   * the request to the mock API.
   */
  async function handleSubmit(e) {
    e.preventDefault();

    onError("");
    onLoadingChange(true);

    /* Construct request payload for API */
    const payload = {
      job_title: jobTitle,
      skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
      location,
      experience_level: experience,
    };

    try {

      /* Call mock API */
      const response = await mockSearchJobs(payload);
      onResults(response);

    } catch (requestError) {

      /* Handle API errors */
      onResults([]);
      onError(requestError.message || "Search failed.");

    } finally {

      /* Reset loading state */
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
          required
        />

        {/* Skills input */}
        <input
          placeholder="Skills (comma separated)"
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
          required
        />

        {/* Location input */}
        <input
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          required
        />

        {/* Experience level selection */}
        <select
          value={experience}
          onChange={(e) => setExperience(e.target.value)}
          required
        >
          <option value="Entry">Entry</option>
          <option value="Mid">Mid</option>
          <option value="Senior">Senior</option>
        </select>

        {/* Submit button */}
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Searching..." : "Search Jobs"}
        </button>
      </form>
    </div>
  );
}