#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const os = require("os");

function parseArgs(argv) {
  const args = { _: [], flags: {} };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.replace(/^--/, "");
      const value = argv[i + 1] && !argv[i + 1].startsWith("-") ? argv[++i] : true;
      args.flags[key] = value;
    } else {
      args._.push(a);
    }
  }
  return args;
}

// Get settings path for Gemini
function getSettingsPath() {
  const geminiDir = path.join(os.homedir(), ".gemini");
  if (!fs.existsSync(geminiDir)) fs.mkdirSync(geminiDir);
  return path.join(geminiDir, "settings.json");
}

// Check if an MCP server is from Klavis AI
function isKlavisAiService(serverConfig) {
  if (!serverConfig || !serverConfig.args || !serverConfig.args[1]) {
    return false;
  }
  const url = serverConfig.args[1];
  return url.includes('klavis.ai');
}

// Create backup and cleanup old backups
function createBackup(settingsPath) {
  if (!fs.existsSync(settingsPath)) {
    return;
  }

  const backupPath = `${settingsPath}.bak.${Date.now()}`;
  fs.copyFileSync(settingsPath, backupPath);
  
  // Clean up old backups - keep only 1 most recent
  try {
    const geminiDir = path.dirname(settingsPath);
    const backupFiles = fs.readdirSync(geminiDir)
      .filter(file => file.startsWith('settings.json.bak.'))
      .map(file => ({
        name: file,
        path: path.join(geminiDir, file),
        timestamp: parseInt(file.split('.bak.')[1]) || 0
      }))
      .sort((a, b) => b.timestamp - a.timestamp); // Sort by timestamp, newest first
    
    // Remove backups beyond the 1 most recent
    if (backupFiles.length > 1) {
      const toDelete = backupFiles.slice(1);
      toDelete.forEach(backup => {
        fs.unlinkSync(backup.path);
      });
    }
  } catch (e) {
    // Silently ignore cleanup errors
  }
}

// Show help information
function showHelp() {
  console.log("📚 Klavis AI - MCP Server Manager for Gemini");
  console.log("===========================================");
  console.log("");
  console.log("DESCRIPTION:");
  console.log("  A CLI tool for managing Klavis AI MCP servers in Gemini CLI");
  console.log("");
  console.log("USAGE:");
  console.log("  klavis <command> [options]");
  console.log("");
  console.log("COMMANDS:");
  console.log("  gemini --help                Show this help message");
  console.log("  gemini add <INSTANCE_URL>    Add a Klavis AI MCP server to Gemini");
  console.log("  gemini remove <MCP_NAME>     Remove a Klavis AI MCP server from Gemini");
  console.log("  gemini list                  List all configured Klavis AI MCP servers");
  console.log("  gemini clear --force         Remove all Klavis AI MCP servers from Gemini");
  console.log("");
  console.log("");
  console.log("EXAMPLES:");
  console.log("  # Show help");
  console.log("  klavis gemini --help");
  console.log("");
  console.log("  # Add an MCP server");
  console.log("  klavis gemini add https://myservice-mcp-server.klavis.ai/mcp/?instance_id=your-id");
  console.log("");
  console.log("  # List all configured servers");
  console.log("  klavis gemini list");
  console.log("");
  console.log("  # Remove a specific server");
  console.log("  klavis gemini remove gmail");
  console.log("");
  console.log("  # Clear all Klavis AI servers");
  console.log("  klavis gemini clear --force");
  console.log("");
  console.log("NOTES:");
  console.log("  • Only Klavis AI MCPs can be managed with this tool");
  console.log("  • Settings are stored in ~/.gemini/settings.json");
  console.log("  • Automatic backups are created before modifications");
  console.log("");
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  // Handle help flag
  if (args._[0] === "gemini" && args.flags.help) {
    showHelp();
    return;
  }

  if (args._[0] !== "gemini" || !["add", "remove", "list", "clear", "help"].includes(args._[1])) {
    console.error("Usage: klavis gemini add <INSTANCE_URL> | klavis gemini remove <MCP_NAME> | klavis gemini list | klavis gemini clear --force | klavis gemini --help");
    console.error("For detailed help, run: klavis gemini --help");
    process.exit(1);
  }

  // For add and remove commands, require the third argument
  if ((args._[1] === "add" || args._[1] === "remove") && !args._[2]) {
    console.error("Usage: klavis gemini add <INSTANCE_URL> | klavis gemini remove <MCP_NAME> | klavis gemini list | klavis gemini clear --force | klavis gemini --help");
    process.exit(1);
  }

  // For clear command, require the --force flag
  if (args._[1] === "clear" && !args.flags.force) {
    console.error("❌ Clear command requires --force flag for safety");
    console.error("Usage: klavis gemini clear --force");
    process.exit(1);
  }

  const action = args._[1];
  const input = args._[2];
  let service, instanceUrl;

  if (action === "add") {
    // For add command, expect URL
    instanceUrl = input;
    if (!instanceUrl.startsWith('http')) {
      console.error("❌ Invalid URL format. URL must start with http or https");
      process.exit(1);
    }

    // Extract service name from URL
    const urlMatch = instanceUrl.match(/https?:\/\/([^.]+)\.klavis\.ai/);
    if (!urlMatch) {
      console.error("❌ Invalid URL format. Expected pattern: https://SERVICE-mcp-server.klavis.ai/");
      process.exit(1);
    }
    
    // Check if URL is from Klavis AI
    if (!instanceUrl.includes('klavis.ai')) {
      console.error("❌ Only Klavis AI MCP servers can be added with this tool");
      process.exit(1);
    }
    
    service = urlMatch[1].toLowerCase();
  } else if (action === "remove") {
    // For remove command, expect service name
    service = input.toLowerCase();
  } else if (action === "list") {
    // For list command, no additional input needed
  } else if (action === "clear") {
    // For clear command, no additional input needed
  }

  const settingsPath = getSettingsPath();
  let settings = {};

  // Read existing settings or create fresh
  if (fs.existsSync(settingsPath)) {
    try {
      const rawData = fs.readFileSync(settingsPath, "utf-8");
      // Fix common JSON issues like trailing commas
      const cleanedData = rawData
        .replace(/,(\s*[}\]])/g, '$1')  // Remove trailing commas
        .replace(/([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:/g, '$1"$2":'); // Quote unquoted keys
      
      settings = JSON.parse(cleanedData);
    } catch (e) {
      console.error("❌ Error reading existing settings:", e.message);
      console.error("💡 Try fixing JSON syntax in:", settingsPath);
      process.exit(1);
    }
  }

  settings.mcpServers = settings.mcpServers || {};

  // Handle add, remove, or list action
  if (action === "list") {
    // List only Klavis AI MCP servers
    const mcpServers = settings.mcpServers || {};
    const klavisServerNames = Object.keys(mcpServers).filter(name => 
      isKlavisAiService(mcpServers[name])
    );
    
    if (klavisServerNames.length === 0) {
      console.log("📋 No Klavis AI MCP servers configured in Gemini settings");
      console.log(`💡 Add a server with: klavis gemini add <INSTANCE_URL>`);
      return;
    }
    
    console.log("📋 Available Klavis AI MCP Servers:");
    console.log("===================================");
    
    klavisServerNames.forEach((name, index) => {
      console.log(`${index + 1}. ${name}`);
    });
    
    console.log(`\nTotal: ${klavisServerNames.length} Klavis AI MCP server(s) configured`);
    return;
    
  } else if (action === "clear") {
    // Clear only Klavis AI MCP servers
    const mcpServers = settings.mcpServers || {};
    const klavisServerNames = Object.keys(mcpServers).filter(name => 
      isKlavisAiService(mcpServers[name])
    );
    
    if (klavisServerNames.length === 0) {
      console.log("📋 No Klavis AI MCP servers to clear - configuration is already empty");
      return;
    }
    
    // Backup before clearing
    createBackup(settingsPath);
    
    // Remove only Klavis AI MCP servers
    klavisServerNames.forEach(name => {
      delete settings.mcpServers[name];
    });
    
    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2), "utf-8");
    console.log(`✅ Cleared ${klavisServerNames.length} Klavis AI MCP server(s) from Gemini settings at ${settingsPath}`);
    return;
    
  } else if (action === "add") {
    // Backup before saving
    createBackup(settingsPath);

    // Add new MCP service
    settings.mcpServers[service] = {
      command: "npx",
      args: ["mcp-remote", instanceUrl]
    };

    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2), "utf-8");
    console.log(`✅ Added ${service} MCP to Gemini settings at ${settingsPath}`);
    
  } else if (action === "remove") {
    // Check if service exists
    if (!settings.mcpServers || !settings.mcpServers[service]) {
      console.error(`❌ Service '${service}' not found in Gemini settings`);
      process.exit(1);
    }

    // Check if service is from Klavis AI
    if (!isKlavisAiService(settings.mcpServers[service])) {
      console.error(`❌ Service '${service}' is not a Klavis AI service and cannot be removed with this tool`);
      process.exit(1);
    }

    // Backup before saving
    createBackup(settingsPath);

    // Remove MCP service
    delete settings.mcpServers[service];

    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2), "utf-8");
    console.log(`✅ Removed ${service} MCP from Gemini settings at ${settingsPath}`);
  }
}

main();
