import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import SearchForm from "../SearchForm";
import { searchJobs } from "../../services/api";

vi.mock("../../services/api", () => ({
  searchJobs: vi.fn(),
  uploadResume: vi.fn(),
}));

describe("SearchForm Component", () => {
  const mockProps = {
    onResults: vi.fn(),
    onLoadingChange: vi.fn(),
    onError: vi.fn(),
    onHasSearchedChange: vi.fn(),
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the job search form", () => {
    render(<SearchForm {...mockProps} />);

    expect(screen.getByText("Job Search")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Job Title")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Skills (comma separated)")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Location")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Years of Experience")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search Jobs" })).toBeInTheDocument();
  });

  it("updates input fields when the user types", () => {
    render(<SearchForm {...mockProps} />);

    fireEvent.change(screen.getByPlaceholderText("Job Title"), {
      target: { value: "Frontend Developer" },
    });

    fireEvent.change(screen.getByPlaceholderText("Skills (comma separated)"), {
      target: { value: "React, JavaScript" },
    });

    fireEvent.change(screen.getByPlaceholderText("Location"), {
      target: { value: "Remote" },
    });

    fireEvent.change(screen.getByPlaceholderText("Years of Experience"), {
      target: { value: "2" },
    });

    expect(screen.getByPlaceholderText("Job Title")).toHaveValue("Frontend Developer");
    expect(screen.getByPlaceholderText("Skills (comma separated)")).toHaveValue("React, JavaScript");
    expect(screen.getByPlaceholderText("Location")).toHaveValue("Remote");
    expect(screen.getByPlaceholderText("Years of Experience")).toHaveValue(2);
  });

  it("submits the search form and sends the correct payload", async () => {
    const mockResults = [
      {
        title: "Frontend Developer",
        company: "Tech Co",
        location: "Remote",
        score: 0.9,
        matched_skills: ["React"],
      },
    ];

    searchJobs.mockResolvedValue({ results: mockResults });

    render(<SearchForm {...mockProps} />);

    fireEvent.change(screen.getByPlaceholderText("Job Title"), {
      target: { value: "Frontend Developer" },
    });

    fireEvent.change(screen.getByPlaceholderText("Skills (comma separated)"), {
      target: { value: "React, JavaScript" },
    });

    fireEvent.change(screen.getByPlaceholderText("Location"), {
      target: { value: "Remote" },
    });

    fireEvent.change(screen.getByPlaceholderText("Years of Experience"), {
      target: { value: "2" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Search Jobs" }));

    await waitFor(() => {
      expect(searchJobs).toHaveBeenCalledWith({
        job_title: "Frontend Developer",
        skills: ["React", "JavaScript"],
        location: "Remote",
        experience_level: 2,
      });
    });

    expect(mockProps.onResults).toHaveBeenCalledWith(mockResults);
  });

  it("clears stale UI state before starting a new search", async () => {
    searchJobs.mockResolvedValue({ results: [] });

    render(<SearchForm {...mockProps} />);

    fireEvent.change(screen.getByPlaceholderText("Job Title"), {
      target: { value: "Developer" },
    });

    fireEvent.change(screen.getByPlaceholderText("Skills (comma separated)"), {
      target: { value: "React" },
    });

    fireEvent.change(screen.getByPlaceholderText("Location"), {
      target: { value: "Remote" },
    });

    fireEvent.change(screen.getByPlaceholderText("Years of Experience"), {
      target: { value: "1" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Search Jobs" }));

    expect(mockProps.onResults).toHaveBeenCalledWith([]);
    expect(mockProps.onError).toHaveBeenCalledWith("");
    expect(mockProps.onHasSearchedChange).toHaveBeenCalledWith(true);
    expect(mockProps.onLoadingChange).toHaveBeenCalledWith(true);
  });

  it("shows searching state when isLoading is true", () => {
    render(<SearchForm {...mockProps} isLoading={true} />);

    expect(screen.getByRole("button", { name: "Searching..." })).toBeDisabled();
    expect(screen.getByPlaceholderText("Job Title")).toBeDisabled();
    expect(screen.getByPlaceholderText("Skills (comma separated)")).toBeDisabled();
    expect(screen.getByPlaceholderText("Location")).toBeDisabled();
    expect(screen.getByPlaceholderText("Years of Experience")).toBeDisabled();
  });

  it("handles search errors", async () => {
    searchJobs.mockRejectedValue(new Error("Search request failed."));

    render(<SearchForm {...mockProps} />);

    fireEvent.change(screen.getByPlaceholderText("Job Title"), {
      target: { value: "Developer" },
    });

    fireEvent.change(screen.getByPlaceholderText("Skills (comma separated)"), {
      target: { value: "React" },
    });

    fireEvent.change(screen.getByPlaceholderText("Location"), {
      target: { value: "Remote" },
    });

    fireEvent.change(screen.getByPlaceholderText("Years of Experience"), {
      target: { value: "1" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Search Jobs" }));

    await waitFor(() => {
      expect(mockProps.onError).toHaveBeenCalledWith("Search request failed.");
    });

    expect(mockProps.onResults).toHaveBeenCalledWith([]);
    expect(mockProps.onLoadingChange).toHaveBeenLastCalledWith(false);
  });
});