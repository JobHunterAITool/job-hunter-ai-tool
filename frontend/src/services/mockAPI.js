import mockResults from "../mock/searchResults.json";

export async function mockSearchJobs(payload) {
  console.log("Mock API received payload:", payload);

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockResults);
    }, 500);
  });
}