#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const childProcess = require('child_process');

const BINARY_MAP = {
    darwin_x64:   { name: 'slack-mcp-server-darwin-amd64',    suffix: '' },
    darwin_arm64: { name: 'slack-mcp-server-darwin-arm64',    suffix: '' },
    linux_x64:    { name: 'slack-mcp-server-linux-amd64',     suffix: '' },
    linux_arm64:  { name: 'slack-mcp-server-linux-arm64',     suffix: '' },
    win32_x64:    { name: 'slack-mcp-server-windows-amd64',   suffix: '.exe' },
    win32_arm64:  { name: 'slack-mcp-server-windows-arm64',   suffix: '.exe' },
};

function resolveBinaryPath() {
    // If DXT installation then we fix empty variables, it's a DXT bug.
    if (process.env.SLACK_MCP_DXT) {
        if (process.env.SLACK_MCP_XOXC_TOKEN === '${user_config.xoxc_token}') {
            process.env.SLACK_MCP_XOXC_TOKEN = '';
        }
        if (process.env.SLACK_MCP_XOXD_TOKEN === '${user_config.xoxd_token}') {
            process.env.SLACK_MCP_XOXD_TOKEN = '';
        }
        if (process.env.SLACK_MCP_XOXP_TOKEN === '${user_config.xoxp_token}') {
            process.env.SLACK_MCP_XOXP_TOKEN = '';
        }
        if (process.env.SLACK_MCP_ADD_MESSAGE_TOOL === '${user_config.add_message_tool}') {
            process.env.SLACK_MCP_ADD_MESSAGE_TOOL = '';
        }
    }

    const key = `${process.platform}_${process.arch}`;
    const binary = BINARY_MAP[key];
    if (!binary) {
        throw new Error(`Could not resolve binary for platform/arch: ${process.platform}/${process.arch}`);
    }

    if (process.env.SLACK_MCP_DXT) {
        return require.resolve(path.join(__dirname, `${binary.name}${binary.suffix}`));
    } else {
        return require.resolve(`${binary.name}/bin/${binary.name}${binary.suffix}`);
    }
}

const binPath = resolveBinaryPath();

// Workaround for https://github.com/anthropics/dxt/issues/13
if (process.env.SLACK_MCP_DXT) {
    const stats = fs.statSync(binPath);
    const execMask = fs.constants.S_IXUSR
        | fs.constants.S_IXGRP
        | fs.constants.S_IXOTH;

    if ((stats.mode & execMask) !== execMask) {
        const newMode = stats.mode | execMask;
        fs.chmodSync(binPath, newMode);
    }
}

childProcess.execFileSync(binPath, process.argv.slice(2), {
    stdio: 'inherit',
});
