/**
 * Mock API
 *
 * Simulates a backend job search API request for development and testing.
 *
 * Author: Carl Ikai
 * Project: Job Hunter AI Tool
 */

import mockResults from "../mock/searchResults.json";

export async function mockSearchJobs(payload) {
  console.log("Mock API received payload:", payload);

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockResults);
    }, 500);
  });
}
export async function uploadResume(file) {
  console.log("Mock resume upload received:", file.name);

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        filename: file.name,
        preview: "This is a mock resume preview. Backend parsing is not being used right now.",
      });
    }, 500);
  });
}