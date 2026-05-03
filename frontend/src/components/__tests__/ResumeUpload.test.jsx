import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import ResumeUpload from "../ResumeUpload";
import { uploadResume } from "../../services/mockAPI";

vi.mock("../../services/mockAPI", () => ({
  uploadResume: vi.fn(),
}));

function getFileInput() {
  return document.querySelector('input[type="file"]');
}

describe("ResumeUpload Component", () => {
  it("renders the resume upload section", () => {
    render(<ResumeUpload />);

    expect(screen.getByText("Resume Upload")).toBeInTheDocument();
    expect(screen.getByText(/Drop Resume Here/i)).toBeInTheDocument();
    expect(screen.getByText("Browse Files")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Upload Resume" })
    ).toBeInTheDocument();
  });

  it("shows an error when upload is clicked without selecting a file", () => {
    render(<ResumeUpload />);

    fireEvent.click(screen.getByRole("button", { name: "Upload Resume" }));

    expect(
      screen.getByText("Please select a resume file first.")
    ).toBeInTheDocument();
  });

  it("accepts a PDF file and displays the selected file name", () => {
    render(<ResumeUpload />);

    const file = new File(["resume text"], "resume.pdf", {
      type: "application/pdf",
    });

    fireEvent.change(getFileInput(), {
      target: { files: [file] },
    });

    expect(screen.getByText("Selected file: resume.pdf")).toBeInTheDocument();
  });

  it("accepts a DOCX file and displays the selected file name", () => {
    render(<ResumeUpload />);

    const file = new File(["resume text"], "resume.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    fireEvent.change(getFileInput(), {
      target: { files: [file] },
    });

    expect(screen.getByText("Selected file: resume.docx")).toBeInTheDocument();
  });

  it("rejects invalid file types", () => {
    render(<ResumeUpload />);

    const file = new File(["not a resume"], "resume.txt", {
      type: "text/plain",
    });

    fireEvent.change(getFileInput(), {
      target: { files: [file] },
    });

    expect(
      screen.getByText("Please upload a PDF or DOCX resume.")
    ).toBeInTheDocument();
  });

  it("uploads a selected file and displays preview text", async () => {
    uploadResume.mockResolvedValue({
      filename: "resume.pdf",
      preview: "Mock resume preview text.",
    });

    render(<ResumeUpload />);

    const file = new File(["resume text"], "resume.pdf", {
      type: "application/pdf",
    });

    fireEvent.change(getFileInput(), {
      target: { files: [file] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Resume" }));

    expect(
      screen.getByRole("button", { name: "Uploading..." })
    ).toBeDisabled();

    await waitFor(() => {
      expect(screen.getByText("Resume Preview")).toBeInTheDocument();
      expect(screen.getByText("Mock resume preview text.")).toBeInTheDocument();
    });

    expect(uploadResume).toHaveBeenCalledWith(file);
  });

  it("shows an error if upload fails", async () => {
    uploadResume.mockRejectedValue(new Error("Resume upload failed."));

    render(<ResumeUpload />);

    const file = new File(["resume text"], "resume.pdf", {
      type: "application/pdf",
    });

    fireEvent.change(getFileInput(), {
      target: { files: [file] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Resume" }));

    await waitFor(() => {
      expect(screen.getByText("Resume upload failed.")).toBeInTheDocument();
    });
  });
});