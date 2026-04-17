import { useState } from "react";

export default function SearchForm() {
  const [jobTitle, setJobTitle] = useState("");
  const [skills, setSkills] = useState("");
  const [location, setLocation] = useState("");
  const [experience, setExperience] = useState("");

  function handleSubmit(e) {
    e.preventDefault();

    const payload = {
      job_title: jobTitle,
      skills: skills.split(",").map(s => s.trim()),
      location: location,
      experience_level: experience
    };

    console.log("Search payload:", payload);
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Job Search</h2>

      <input
        placeholder="Job Title"
        value={jobTitle}
        onChange={(e) => setJobTitle(e.target.value)}
      />

      <input
        placeholder="Skills (comma separated)"
        value={skills}
        onChange={(e) => setSkills(e.target.value)}
      />

      <input
        placeholder="Location"
        value={location}
        onChange={(e) => setLocation(e.target.value)}
      />

      <select
        value={experience}
        onChange={(e) => setExperience(e.target.value)}
      >
        <option value="">Select Experience</option>
        <option value="entry">Entry</option>
        <option value="mid">Mid</option>
        <option value="senior">Senior</option>
      </select>

      <button type="submit">Search Jobs</button>
    </form>
  );
}