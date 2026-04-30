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
import { mockSearchJobs } from "../services/mockAPI";
import ResumeUpload from "./ResumeUpload";

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
   * the request to the backend API.
   */
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

      /*
       * Supports either:
       * 1. Backend returns an array directly
       * 2. Backend returns { results: [...] }
       */
      onResults(Array.isArray(response) ? response : response.results || []);
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

      <ResumeUpload />
    </div>
  );
}