import { defineConfig } from "vitest/config";
import { BaseSequencer } from "vitest/node";

// Custom sequencer that puts kubectl.test.ts at the end
class KubectlSequencer extends BaseSequencer {
  // Override the sort method to place kubectl tests last
  async sort(files) {
    // Get default sorted files
    const sortedFiles = await super.sort(files);

    sortedFiles.forEach((file) => {
      console.log(file.moduleId);
    });

    // Split into kubectl tests and other tests
    const kubectlTests = sortedFiles.filter((f) =>
      f.moduleId.includes("kubectl.test.ts")
    );
    const otherTests = sortedFiles.filter(
      (f) => !f.moduleId.includes("kubectl.test.ts")
    );

    // Return other tests first, then kubectl tests
    return [...otherTests, ...kubectlTests];
  }
}

export default defineConfig({
  test: {
    testTimeout: 120000,
    hookTimeout: 60000,
    exclude: ["dist/**/*", "node_modules/**/*"],
    sequence: {
      sequencer: KubectlSequencer,
    },
  },
});
