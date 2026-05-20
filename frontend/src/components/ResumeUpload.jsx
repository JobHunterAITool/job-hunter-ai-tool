/**
 * ResumeUpload Component
 *
 * Allows users to drag and drop a PDF or DOCX resume and sends it
 * to the backend for text preview extraction.
 *
 * Author: Carl Ikai
 * Project: Job Hunter AI Tool
 */

import { useEffect, useState } from "react";
import { uploadResume, searchJobs } from "../services/api";

export default function ResumeUpload({
  resetKey,
  onClearSearchFields,
  onResults,
  onLoadingChange,
  onError,
  onHasSearchedChange,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  /**
   * Clear upload UI when a normal search is performed.
   */
  useEffect(() => {
    setSelectedFile(null);
    setPreview("");
    setError("");
    setIsDragging(false);
  }, [resetKey]);

  function isValidResumeFile(file) {
    const fileName = file.name.toLowerCase();
    return fileName.endsWith(".pdf") || fileName.endsWith(".docx");
  }

  function handleSelectedFile(file) {
    if (!file) return;

    if (!isValidResumeFile(file)) {
      setError("Please upload a PDF or DOCX resume.");
      setSelectedFile(null);
      return;
    }

    setError("");
    setPreview("");
    setSelectedFile(file);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    handleSelectedFile(droppedFile);
  }

  async function handleUpload(e) {
    e.preventDefault();

    if (!selectedFile) {
      setError("Please select a resume file first.");
      return;
    }

    setError("");
    setPreview("");
    setIsUploading(true);

    if (onResults) onResults([]);
    if (onError) onError("");
    if (onHasSearchedChange) onHasSearchedChange(true);
    if (onLoadingChange) onLoadingChange(true);

    try {
      const data = await uploadResume(selectedFile);

      /* Clear manual search fields after resume upload */
      if (onClearSearchFields) {
        onClearSearchFields();
      }

      setPreview(
        data.extracted_text_preview ||
          "No preview text could be extracted."
      );

      if (data.profile) {
        const response = await searchJobs(data.profile);

        const searchResults = Array.isArray(response)
          ? response
          : response.results || [];

        if (onResults) {
          onResults(searchResults);
        }
      }
    } catch (uploadError) {
      if (onResults) onResults([]);

      setError(uploadError.message || "Something went wrong.");

      if (onError) {
        onError(uploadError.message || "Something went wrong.");
      }
    } finally {
      setIsUploading(false);

      if (onLoadingChange) {
        onLoadingChange(false);
      }
    }
  }

  return (
    <div className="resume-upload-section">
      <h2>Resume Upload</h2>

      <form className="resume-upload-form" onSubmit={handleUpload}>
        <div
          className={`resume-drop-zone ${
            isDragging ? "drag-active" : ""
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <div className="drop-zone-content">
            <p className="drop-title">📄 Drop Resume Here</p>

            <p className="drop-subtitle">
              Drag & drop a PDF or DOCX resume
            </p>

            <label className="file-select-label">
              Browse Files

              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(e) =>
                  handleSelectedFile(e.target.files[0])
                }
                hidden
              />
            </label>
          </div>
        </div>

        {selectedFile && (
          <p className="selected-file">
            Selected file: {selectedFile.name}
          </p>
        )}

        <button type="submit" disabled={isUploading}>
          {isUploading ? "Uploading..." : "Upload Resume"}
        </button>
      </form>

      {error && <p className="error-message">{error}</p>}

      {preview && (
        <div className="resume-preview">
          <h3>Resume Preview</h3>

          <p style={{ whiteSpace: "pre-line" }}>{preview}</p>
        </div>
      )}
    </div>
  );
}