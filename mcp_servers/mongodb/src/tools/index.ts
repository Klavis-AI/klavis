// import * as AtlasTools from "./atlas/tools.js";
// import * as AtlasLocalTools from "./atlasLocal/tools.js";
import * as MongoDbTools from "./mongodb/tools.js";
import type { ToolClass } from "./tool.js";

// Export the collection of tools for easier reference
export const AllTools: ToolClass[] = Object.values({
    ...MongoDbTools,
    // ...AtlasTools,
    // ...AtlasLocalTools,
});

// Export all the individual tools for handpicking
// export * from "./atlas/tools.js";
// export * from "./atlasLocal/tools.js";
export * from "./mongodb/tools.js";

// Export the base tool class and supporting types.
export {
    ToolBase,
    type ToolClass,
    type ToolConstructorParams,
    type ToolCategory,
    type OperationType,
    type ToolArgs,
    type ToolExecutionContext,
} from "./tool.js";
