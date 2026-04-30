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

    onError("");
    onLoadingChange(true);

    const payload = {
      job_title: jobTitle,
      skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
      location,
      experience_level: experience, // backend still expects this field
    };

    try {
      const response = await searchJobs(payload);

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

        {/* Years of experience typed input */}
        <input
          type="number"
          placeholder="Years of Experience"
          value={experience}
          onChange={(e) => setExperience(e.target.value)}
          min="0"
          required
        />

        {/* Submit button */}
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Searching..." : "Search Jobs"}
        </button>
      </form>

      <ResumeUpload />
    </div>
  );
}