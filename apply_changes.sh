#!/bin/bash
set -e
cat > .github/workflows/typescript-sdk-release.yml.tmp << 'EOF'
name: Typescript SDK Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release'
        required: true
        type: string

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Generate and Publish SDK
        env:
          FERN_TOKEN: ${{ secrets.FERN_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
          VERSION: ${{ inputs.version }}
        run: |
          fern generate --group ts-sdk --version "$VERSION" --log-level debug

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
EOF
mv .github/workflows/typescript-sdk-release.yml.tmp .github/workflows/typescript-sdk-release.yml