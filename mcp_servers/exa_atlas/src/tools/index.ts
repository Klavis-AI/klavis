// Export the tool registry
export { toolRegistry, API_CONFIG, asyncLocalStorage, getApiKey } from "./config.js";

// Import all tools to register them
import "./webSearch.js";
import "./researchPaperSearch.js";
import "./companyResearch.js";
import "./crawling.js";
import "./competitorFinder.js";
import "./linkedInSearch.js";
import "./wikipediaSearch.js";
import "./githubSearch.js";

// When adding a new tool, import it here
// import "./newTool.js"; 