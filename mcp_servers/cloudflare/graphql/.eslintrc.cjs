/** @type {import("eslint").Linter.Config} */
module.exports = {
	root: false,
	extends: [
		"../.eslintrc.js"
	],
	parserOptions: {
		tsconfigRootDir: ".",
		project: "./tsconfig.json"
	},
	rules: {
		// Package-specific rules can go here
	}
}
