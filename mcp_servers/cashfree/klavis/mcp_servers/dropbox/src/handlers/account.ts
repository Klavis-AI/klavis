import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";

export async function handleGetCurrentAccount(args: any) {
    schemas.GetCurrentAccountSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.usersGetCurrentAccount();
    const account = response.result as any;

    // Build comprehensive account information
    let accountInfo = `=== Dropbox Account Information ===\n\n`;

    // Basic Information
    accountInfo += `Account ID: ${account.account_id || 'Unknown'}\n`;
    accountInfo += `Email: ${account.email || 'Unknown'}\n`;
    accountInfo += `Email Verified: ${account.email_verified ? 'Yes' : 'No'}\n`;
    accountInfo += `Account Disabled: ${account.disabled ? 'Yes' : 'No'}\n`;
    accountInfo += `Locale: ${account.locale || 'Unknown'}\n`;
    accountInfo += `Country: ${account.country || 'Unknown'}\n`;

    // Name Information
    if (account.name) {
        accountInfo += `\n--- Name Details ---\n`;
        accountInfo += `Display Name: ${account.name.display_name || 'Unknown'}\n`;
        accountInfo += `Given Name: ${account.name.given_name || 'Unknown'}\n`;
        accountInfo += `Surname: ${account.name.surname || 'Unknown'}\n`;
        accountInfo += `Familiar Name: ${account.name.familiar_name || 'Unknown'}\n`;
        accountInfo += `Abbreviated Name: ${account.name.abbreviated_name || 'Unknown'}\n`;
    }

    // Account Type
    if (account.account_type) {
        accountInfo += `\n--- Account Type ---\n`;
        accountInfo += `Type: ${account.account_type['.tag'] || 'Unknown'}\n`;
    }

    // Profile and Links
    accountInfo += `\n--- Profile & Links ---\n`;
    accountInfo += `Referral Link: ${account.referral_link || 'Not available'}\n`;
    if (account.profile_photo_url) {
        accountInfo += `Profile Photo: ${account.profile_photo_url}\n`;
    }

    // Pairing Information
    accountInfo += `\n--- Account Pairing ---\n`;
    accountInfo += `Is Paired (has work account): ${account.is_paired ? 'Yes' : 'No'}\n`;

    // Root Information
    if (account.root_info) {
        accountInfo += `\n--- Root Information ---\n`;
        accountInfo += `Root Type: ${account.root_info['.tag'] || 'Unknown'}\n`;
        accountInfo += `Home Namespace ID: ${account.root_info.home_namespace_id || 'Unknown'}\n`;
        accountInfo += `Root Namespace ID: ${account.root_info.root_namespace_id || 'Unknown'}\n`;
    }

    // Team Information (if applicable)
    if (account.team) {
        accountInfo += `\n--- Team Information ---\n`;
        accountInfo += `Team ID: ${account.team.id || 'Unknown'}\n`;
        accountInfo += `Team Name: ${account.team.name || 'Unknown'}\n`;
        if (account.team_member_id) {
            accountInfo += `Team Member ID: ${account.team_member_id}\n`;
        }

        // Team Policies
        if (account.team.sharing_policies) {
            accountInfo += `\n--- Team Sharing Policies ---\n`;
            const policies = account.team.sharing_policies;
            if (policies.shared_link_create_policy) {
                accountInfo += `Shared Link Creation: ${policies.shared_link_create_policy['.tag'] || 'Unknown'}\n`;
            }
            if (policies.shared_folder_member_policy) {
                accountInfo += `Shared Folder Member Policy: ${policies.shared_folder_member_policy['.tag'] || 'Unknown'}\n`;
            }
            if (policies.shared_folder_join_policy) {
                accountInfo += `Shared Folder Join Policy: ${policies.shared_folder_join_policy['.tag'] || 'Unknown'}\n`;
            }
            if (policies.enforce_link_password_policy) {
                accountInfo += `Link Password Policy: ${policies.enforce_link_password_policy['.tag'] || 'Unknown'}\n`;
            }
            if (policies.default_link_expiration_days_policy) {
                accountInfo += `Default Link Expiration: ${policies.default_link_expiration_days_policy['.tag'] || 'Unknown'}\n`;
            }
        }

        if (account.team.office_addin_policy) {
            accountInfo += `Office Add-in Policy: ${account.team.office_addin_policy['.tag'] || 'Unknown'}\n`;
        }

        if (account.team.top_level_content_policy) {
            accountInfo += `Top Level Content Policy: ${account.team.top_level_content_policy['.tag'] || 'Unknown'}\n`;
        }
    }

    return {
        content: [
            {
                type: "text",
                text: accountInfo,
            },
        ],
    };
}

export async function handleGetSpaceUsage(args: any) {
    schemas.GetSpaceUsageSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.usersGetSpaceUsage();
    const spaceInfo = response.result as any;
    let info = `Used: ${spaceInfo.used} bytes`;
    if (spaceInfo.allocation) {
        if (spaceInfo.allocation['.tag'] === 'individual') {
            info += `\nAllocated: ${spaceInfo.allocation.allocated} bytes`;
        } else {
            info += `\nAllocation Type: ${spaceInfo.allocation['.tag']}`;
        }
    }

    return {
        content: [
            {
                type: "text",
                text: info,
            },
        ],
    };
}

/**
 * Main handler for account operations
 */
export async function handleAccountOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "dropbox_get_current_account":
            return await handleGetCurrentAccount(args) as CallToolResult;
        case "dropbox_get_space_usage":
            return await handleGetSpaceUsage(args) as CallToolResult;
        default:
            throw new Error(`Unknown account operation: ${name}`);
    }
}
