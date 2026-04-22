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