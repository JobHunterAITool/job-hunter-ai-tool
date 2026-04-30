import axios from "axios";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).trim();

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

/**
 * Sends job search input to the backend search endpoint.
 */
export async function searchJobs(payload) {
  try {
    const response = await apiClient.post("/search", payload);
    return response.data;
  } catch (error) {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      "Search request failed.";

    throw new Error(message);
  }
}

/**
 * Uploads a resume file to the backend upload endpoint.
 */
export async function uploadResume(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await apiClient.post("/upload-resume", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  } catch (error) {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      "Resume upload failed.";

    throw new Error(message);
  }
}