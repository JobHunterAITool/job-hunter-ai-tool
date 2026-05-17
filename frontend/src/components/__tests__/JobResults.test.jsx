import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import "@testing-library/jest-dom/vitest";
import JobResults from "../JobResults";

describe("JobResults Component", () => {
  it("renders the ranked results section", () => {
    render(<JobResults />);

    expect(screen.getByText("Ranked Results")).toBeInTheDocument();
  });

  it("shows the first time empty message before searching", () => {
    render(<JobResults results={[]} isLoading={false} error="" hasSearched={false} />);

    expect(
      screen.getByText("Submit a search to see ranked job matches.")
    ).toBeInTheDocument();
  });

  it("shows loading message while searching", () => {
    render(<JobResults results={[]} isLoading={true} error="" hasSearched={false} />);

    expect(
      screen.getByText("Searching for ranked job matches...")
    ).toBeInTheDocument();
  });

  it("shows an error message when search fails", () => {
    render(
      <JobResults
        results={[]}
        isLoading={false}
        error="Search failed."
        hasSearched={true}
      />
    );

    expect(screen.getByText("Search failed.")).toBeInTheDocument();
  });

  it("shows no results message after a completed search with no jobs", () => {
    render(<JobResults results={[]} isLoading={false} error="" hasSearched={true} />);

    expect(
      screen.getByText("No matching jobs found. Try changing the title, location, or skills.")
    ).toBeInTheDocument();
  });

  it("renders job result cards", () => {
    const mockResults = [
      {
        title: "Frontend Developer",
        company: "Tech Co",
        location: "Remote",
        score: 0.92,
        matched_skills: ["React", "JavaScript"],
      },
    ];

    render(
      <JobResults
        results={mockResults}
        isLoading={false}
        error=""
        hasSearched={true}
      />
    );

    expect(screen.getByText("Frontend Developer")).toBeInTheDocument();
    expect(screen.getByText(/Tech Co/i)).toBeInTheDocument();
    expect(screen.getByText(/Remote/i)).toBeInTheDocument();
    expect(screen.getByText("Score: 0.92")).toBeInTheDocument();
    expect(screen.getByText("Matched skills: React, JavaScript")).toBeInTheDocument();
  });

  it("shows None when a job has no matched skills", () => {
    const mockResults = [
      {
        title: "Backend Developer",
        company: "Server Co",
        location: "Boston, MA",
        score: 0.75,
        matched_skills: [],
      },
    ];

    render(
      <JobResults
        results={mockResults}
        isLoading={false}
        error=""
        hasSearched={true}
      />
    );

    expect(screen.getByText("Matched skills: None")).toBeInTheDocument();
  });
});