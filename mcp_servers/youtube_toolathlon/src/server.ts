import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { VideoService } from './services/video.js';
import { TranscriptService } from './services/transcript.js';
import { PlaylistService } from './services/playlist.js';
import { ChannelService } from './services/channel.js';
import {
    VideoParams,
    SearchParams,
    TranscriptParams,
    ChannelParams,
    ChannelVideosParams,
    ChannelVideosNavParams,
    PlaylistParams,
    PlaylistItemsParams,
} from './types.js';

export async function startMcpServer() {
    const server = new Server(
        {
            name: 'zubeid-youtube-mcp-server',
            version: '1.0.0',
        },
        {
            capabilities: {
                tools: {},
            },
        }
    );

    const videoService = new VideoService();
    const transcriptService = new TranscriptService();
    const playlistService = new PlaylistService();
    const channelService = new ChannelService();

    server.setRequestHandler(ListToolsRequestSchema, async () => {
        return {
            tools: [
                {
                    name: 'videos_getVideo',
                    description: 'Get detailed information about a YouTube video',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            videoId: {
                                type: 'string',
                                description: 'The YouTube video ID',
                            },
                            parts: {
                                type: 'array',
                                description: 'Parts of the video to retrieve',
                                items: {
                                    type: 'string',
                                },
                            },
                        },
                        required: ['videoId'],
                    },
                },
                {
                    name: 'videos_searchVideos',
                    description: 'Search for videos on YouTube',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            query: {
                                type: 'string',
                                description: 'Search query',
                            },
                            maxResults: {
                                type: 'number',
                                description: 'Maximum number of results to return',
                            },
                        },
                        required: ['query'],
                    },
                },
                {
                    name: 'transcripts_getTranscript',
                    description: 'Get the transcript of a YouTube video',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            videoId: {
                                type: 'string',
                                description: 'The YouTube video ID',
                            },
                            language: {
                                type: 'string',
                                description: 'Language code for the transcript',
                            },
                        },
                        required: ['videoId'],
                    },
                },
                {
                    name: 'channels_getChannel',
                    description: 'Get information about a YouTube channel',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            channelId: {
                                type: 'string',
                                description: 'The YouTube channel ID',
                            },
                        },
                        required: ['channelId'],
                    },
                },
                {
                    name: 'channels_listVideos',
                    description: 'Start a new channel videos list with sorting options (creates a new list session)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            channelId: {
                                type: 'string',
                                description: 'The YouTube channel ID',
                            },
                            maxResults: {
                                type: 'number',
                                description: 'Maximum number of results per page (max 20, default 20)',
                                maximum: 20
                            },
                            sortOrder: {
                                type: 'string',
                                description: 'Sort order for videos',
                                enum: ['newest', 'oldest', 'popular']
                            },
                        },
                        required: ['channelId'],
                    },
                },
                {
                    name: 'channels_navigateList',
                    description: 'Navigate within an existing list session (prev/next page, jump to specific page)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            listId: {
                                type: 'string',
                                description: 'The list session ID from a previous listVideos call',
                            },
                            page: {
                                type: 'number',
                                description: 'Page number to navigate to (1-based)',
                                minimum: 1
                            },
                        },
                        required: ['listId', 'page'],
                    },
                },
                {
                    name: 'playlists_getPlaylist',
                    description: 'Get information about a YouTube playlist',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            playlistId: {
                                type: 'string',
                                description: 'The YouTube playlist ID',
                            },
                        },
                        required: ['playlistId'],
                    },
                },
                {
                    name: 'playlists_getPlaylistItems',
                    description: 'Get videos in a YouTube playlist',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            playlistId: {
                                type: 'string',
                                description: 'The YouTube playlist ID',
                            },
                            maxResults: {
                                type: 'number',
                                description: 'Maximum number of results to return',
                            },
                        },
                        required: ['playlistId'],
                    },
                },
                {
                    name: 'playlists_searchPlaylists',
                    description: 'Search for playlists on YouTube',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            query: {
                                type: 'string',
                                description: 'Search query for playlists',
                            },
                            maxResults: {
                                type: 'number',
                                description: 'Maximum number of results to return',
                            },
                        },
                        required: ['query'],
                    },
                },
            ],
        };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        try {
            switch (name) {
                case 'videos_getVideo': {
                    const result = await videoService.getVideo(args as unknown as VideoParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                case 'videos_searchVideos': {
                    const result = await videoService.searchVideos(args as unknown as SearchParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                case 'transcripts_getTranscript': {
                    const result = await transcriptService.getTranscript(args as unknown as TranscriptParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                case 'channels_getChannel': {
                    const result = await channelService.getChannel(args as unknown as ChannelParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                case 'channels_listVideos': {
                    const result = await channelService.listVideos(args as unknown as ChannelVideosParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                case 'channels_navigateList': {
                    const result = await channelService.navigateList(args as unknown as ChannelVideosNavParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                case 'playlists_getPlaylist': {
                    const result = await playlistService.getPlaylist(args as unknown as PlaylistParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                case 'playlists_getPlaylistItems': {
                    const result = await playlistService.getPlaylistItems(args as unknown as PlaylistItemsParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                case 'playlists_searchPlaylists': {
                    const result = await playlistService.searchPlaylists(args as unknown as SearchParams);
                    return {
                        content: [{
                            type: 'text',
                            text: JSON.stringify(result, null, 2)
                        }]
                    };
                }
                
                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (error) {
            return {
                content: [{
                    type: 'text',
                    text: `Error: ${error instanceof Error ? error.message : String(error)}`
                }],
                isError: true
            };
        }
    });

    // Create transport and connect
    const transport = new StdioServerTransport();
    await server.connect(transport);
    
    // Log the server info
    console.log(`YouTube MCP Server v1.0.0 started successfully`);
    console.log(`Server will validate YouTube API key when tools are called`);
    
    return server;
}
