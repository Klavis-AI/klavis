import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { CopyButton } from './ui/copy-button';
import hfLogoWithTitle from '../hf-logo-with-title.svg';
import {
	Copy,
	Settings,
	Search,
	Rocket,
	ChevronDown,
	ChevronRight,
	ExternalLink,
	Download,
	AlertTriangle,
	Info,
} from 'lucide-react';
import { useState } from 'react';
import { ToolPresetsCard } from './bouquets/ToolPresetsCard';

interface ActionButton {
	type: 'link' | 'download' | 'copy' | 'external';
	label: string;
	url?: string;
	content?: string;
	variant?: 'default' | 'secondary' | 'outline';
}

interface InstructionStep {
	type: 'text' | 'code' | 'button' | 'warning' | 'info';
	content: string | React.ReactNode;
	button?: ActionButton;
	copyable?: boolean;
}

interface ClientConfig {
	id: string;
	name: string;
	icon: React.ReactNode;
	description?: string;
	configExample?: string;
	instructions: (string | InstructionStep)[];
	actionButtons?: ActionButton[];
	manualConfig?: {
		title: string;
		steps: InstructionStep[];
	};
}

const CLIENT_CONFIGS: ClientConfig[] = [
	{
		id: 'claude',
		name: 'Claude Desktop and Claude.ai',
		icon: (
			<svg
				className="h-5 w-5"
				width="1em"
				height="1em"
				viewBox="0 0 12 12"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<g clip-path="url(#a)">
					<path
						d="m2.96 7.65 1.97-1.1.03-.1-.03-.05h-.1l-.33-.02-1.12-.03-.97-.04-.95-.06-.24-.05L1 5.91l.02-.15.2-.13.29.02.63.05.95.06.69.04 1.02.11h.16L5 5.84l-.06-.04-.04-.04-.99-.66-1.06-.7-.56-.41-.3-.2-.15-.2-.07-.42.28-.3.36.03.1.02.37.29.8.61 1.03.77.16.12.06-.04v-.03l-.06-.11-.57-1.02-.6-1.04-.27-.43-.07-.26c-.03-.1-.04-.2-.04-.3l.3-.42L3.8 1l.42.06.17.15.26.59.42.93.64 1.26.2.37.1.35.03.1h.07v-.06l.05-.7.1-.88.1-1.12.03-.32.16-.38.3-.2.25.11.2.29-.03.18-.12.77-.23 1.21-.15.81h.09l.1-.1.41-.54.69-.86.3-.34.36-.38.22-.18h.43l.32.47-.14.49-.44.56-.37.47-.53.71-.33.57.03.04h.08l1.2-.26.63-.11.77-.13.35.16.04.16-.14.34-.82.2-.96.2-1.44.33-.01.01.02.03.64.06.28.02h.68l1.25.09.33.22.2.26-.03.2-.5.26-.7-.16-1.59-.38-.54-.13h-.08v.04l.46.45.83.75 1.05.97.05.24-.13.2-.15-.03-.92-.69-.35-.31-.8-.68h-.06v.08l.19.27.98 1.46.05.45-.07.15-.26.09-.28-.05-.57-.8-.59-.9-.47-.82-.06.04-.28 3.02-.13.15-.3.12-.26-.2-.14-.3.14-.62.16-.8.13-.64.12-.79.07-.26v-.02H5.9l-.6.83-.9 1.22-.73.77-.17.07-.3-.15.03-.28.17-.24 1-1.27.6-.78.38-.46v-.06h-.03L2.72 8.73l-.47.06-.2-.19.02-.3.1-.1.8-.55Z"
						fill="#D97757"
					></path>
				</g>
				<defs>
					<clipPath id="a">
						<path fill="#fff" transform="translate(1 1)" d="M0 0h10v10H0z"></path>
					</clipPath>
				</defs>
			</svg>
		),
		instructions: [
			{
				type: 'text',
				content: '1. Click below to open Claude Connectors',
			},
			{
				type: 'text',
				content: (
					<a
						href="https://claude.ai/settings/connectors"
						target="_blank"
						rel="noopener noreferrer"
						className="inline-flex items-center space-x-2 border border-border rounded-lg p-2 hover:bg-accent/10 transition-colors duration-200"
					>
						<svg
							className="h-8 w-8 hover:scale-105 transition-transform duration-200"
							width="1em"
							height="1em"
							viewBox="0 0 12 12"
							fill="none"
							xmlns="http://www.w3.org/2000/svg"
						>
							<g clipPath="url(#a)">
								<path
									d="m2.96 7.65 1.97-1.1.03-.1-.03-.05h-.1l-.33-.02-1.12-.03-.97-.04-.95-.06-.24-.05L1 5.91l.02-.15.2-.13.29.02.63.05.95.06.69.04 1.02.11h.16L5 5.84l-.06-.04-.04-.04-.99-.66-1.06-.7-.56-.41-.3-.2-.15-.2-.07-.42.28-.3.36.03.1.02.37.29.8.61 1.03.77.16.12.06-.04v-.03l-.06-.11-.57-1.02-.6-1.04-.27-.43-.07-.26c-.03-.1-.04-.2-.04-.3l.3-.42L3.8 1l.42.06.17.15.26.59.42.93.64 1.26.2.37.1.35.03.1h.07v-.06l.05-.7.1-.88.1-1.12.03-.32.16-.38.3-.2.25.11.2.29-.03.18-.12.77-.23 1.21-.15.81h.09l.1-.1.41-.54.69-.86.3-.34.36-.38.22-.18h.43l.32.47-.14.49-.44.56-.37.47-.53.71-.33.57.03.04h.08l1.2-.26.63-.11.77-.13.35.16.04.16-.14.34-.82.2-.96.2-1.44.33-.01.01.02.03.64.06.28.02h.68l1.25.09.33.22.2.26-.03.2-.5.26-.7-.16-1.59-.38-.54-.13h-.08v.04l.46.45.83.75 1.05.97.05.24-.13.2-.15-.03-.92-.69-.35-.31-.8-.68h-.06v.08l.19.27.98 1.46.05.45-.07.15-.26.09-.28-.05-.57-.8-.59-.9-.47-.82-.06.04-.28 3.02-.13.15-.3.12-.26-.2-.14-.3.14-.62.16-.8.13-.64.12-.79.07-.26v-.02H5.9l-.6.83-.9 1.22-.73.77-.17.07-.3-.15.03-.28.17-.24 1-1.27.6-.78.38-.46v-.06h-.03L2.72 8.73l-.47.06-.2-.19.02-.3.1-.1.8-.55Z"
									fill="#D97757"
								></path>
							</g>
							<defs>
								<clipPath id="a">
									<path fill="#fff" transform="translate(1 1)" d="M0 0h10v10H0z"></path>
								</clipPath>
							</defs>
						</svg>
						<span className="text-sm font-medium">Go to Claude Connectors</span>
					</a>
				),
			},
			{
				type: 'text',
				content: '2. Click "Browse Connectors"',
			},
			{
				type: 'text',
				content: '3. Select "Hugging Face" and click "Add"',
			},
		],
	},
	{
		id: 'vscode',
		name: 'Visual Studio Code',
		icon: (
			<svg
				className="h-5 w-5"
				width="1em"
				height="1em"
				viewBox="0 0 12 12"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<g clipPath="url(#a)">
					<mask id="b" style={{ maskType: 'alpha' }} maskUnits="userSpaceOnUse" x="1" y="1" width="10" height="10">
						<path
							fillRule="evenodd"
							clipRule="evenodd"
							d="M8.1 10.93c.15.06.33.06.49-.02l2.06-.99c.21-.1.35-.32.35-.56V2.64a.63.63 0 0
  0-.35-.56l-2.06-1a.62.62 0 0 0-.71.13L3.94 4.8 2.22 3.5a.42.42 0 0 0-.53.02l-.55.5a.42.42 0 0 0 0 .62L2.62 6 1.14 7.36a.42.42 0 0 0 0
  .61l.55.5c.15.14.37.15.53.03l1.72-1.3 3.94 3.59c.06.06.13.1.21.14Zm.4-7.2L5.51 6l3 2.27V3.73Z"
							fill="#fff"
						></path>
					</mask>
					<g mask="url(#b)">
						<path
							d="m10.64 2.08-2.06-1a.62.62 0 0 0-.7.13L1.12 7.36a.42.42 0 0 0 0 .61l.55.5c.15.14.37.15.53.03l8.12-6.17c.28-.2.67 0
  .67.33v-.02a.63.63 0 0 0-.36-.56Z"
							fill="#0065A9"
						></path>
						<g filter="url(#c)">
							<path
								d="m10.64 9.92-2.06.99a.62.62 0 0 1-.7-.12L1.12 4.64a.42.42 0 0 1 0-.62l.55-.5a.42.42 0 0 1 .53-.02l8.12
  6.16c.28.2.67.01.67-.33v.03c0 .24-.14.45-.36.56Z"
								fill="#007ACC"
							></path>
						</g>
						<g filter="url(#d)">
							<path
								d="M8.59 10.91a.62.62 0 0 1-.71-.12c.23.23.62.07.62-.26V1.46c0-.32-.4-.48-.63-.25a.62.62 0 0 1
  .72-.12l2.06.99c.21.1.35.32.35.56v6.72c0 .24-.14.46-.35.56l-2.06.99Z"
								fill="#1F9CF0"
							></path>
						</g>
						<path
							fillRule="evenodd"
							clipRule="evenodd"
							d="M8.08 10.93c.16.06.34.06.5-.02l2.06-.99c.21-.1.35-.32.35-.56V2.64a.63.63 0 0
  0-.35-.56l-2.06-1a.62.62 0 0 0-.71.13L3.93 4.8 2.2 3.5a.42.42 0 0 0-.53.02l-.55.5a.42.42 0 0 0 0 .62L2.62 6l-1.5 1.36a.42.42 0 0 0 0
  .61l.56.5c.15.14.37.15.53.03l1.72-1.3 3.94 3.59c.06.06.13.1.21.14Zm.41-7.2L5.5 6l3 2.27V3.73Z"
							fill="url(#e)"
							style={{ mixBlendMode: 'overlay' }}
							opacity=".25"
						></path>
					</g>
				</g>
				<defs>
					<filter
						id="c"
						x="-8.27"
						y="-5.85"
						width="28.53"
						height="26.07"
						filterUnits="userSpaceOnUse"
						colorInterpolationFilters="sRGB"
					>
						<feFlood floodOpacity="0" result="BackgroundImageFix"></feFlood>
						<feColorMatrix
							in="SourceAlpha"
							values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
							result="hardAlpha"
						></feColorMatrix>
						<feOffset></feOffset>
						<feGaussianBlur stdDeviation="4.63"></feGaussianBlur>
						<feColorMatrix values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"></feColorMatrix>
						<feBlend mode="overlay" in2="BackgroundImageFix" result="effect1_dropShadow_640_684"></feBlend>
						<feBlend in="SourceGraphic" in2="effect1_dropShadow_640_684" result="shape"></feBlend>
					</filter>
					<filter
						id="d"
						x="-1.38"
						y="-8.24"
						width="21.64"
						height="28.46"
						filterUnits="userSpaceOnUse"
						colorInterpolationFilters="sRGB"
					>
						<feFlood floodOpacity="0" result="BackgroundImageFix"></feFlood>
						<feColorMatrix
							in="SourceAlpha"
							values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
							result="hardAlpha"
						></feColorMatrix>
						<feOffset></feOffset>
						<feGaussianBlur stdDeviation="4.63"></feGaussianBlur>
						<feColorMatrix values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"></feColorMatrix>
						<feBlend mode="overlay" in2="BackgroundImageFix" result="effect1_dropShadow_640_684"></feBlend>
						<feBlend in="SourceGraphic" in2="effect1_dropShadow_640_684" result="shape"></feBlend>
					</filter>
					<linearGradient id="e" x1="5.99" y1="1.02" x2="5.99" y2="10.97" gradientUnits="userSpaceOnUse">
						<stop stopColor="#fff"></stop>
						<stop offset="1" stopColor="#fff" stopOpacity="0"></stop>
					</linearGradient>
					<clipPath id="a">
						<path fill="#fff" transform="translate(1 1)" d="M0 0h10v10H0z"></path>
					</clipPath>
				</defs>
			</svg>
		),
		//	description: 'Use with VS Code MCP extension',
		instructions: [
			{
				type: 'text',
				content: (
					<a
						href="vscode:mcp/install?%7B%22name%22%3A%22huggingface%22%2C%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fhuggingface.co%2Fmcp%3Flogin%22%7D"
						className="inline-flex items-center space-x-2 border border-border rounded-lg p-2 hover:bg-accent/10 transition-colors duration-200"
					>
						<svg
							className="h-8 w-8 hover:scale-105 transition-transform duration-200"
							width="1em"
							height="1em"
							viewBox="0 0 12 12"
							fill="none"
							xmlns="http://www.w3.org/2000/svg"
						>
							<g clipPath="url(#a)">
								<mask
									id="b"
									style={{ maskType: 'alpha' }}
									maskUnits="userSpaceOnUse"
									x="1"
									y="1"
									width="10"
									height="10"
								>
									<path
										fillRule="evenodd"
										clipRule="evenodd"
										d="M8.1 10.93c.15.06.33.06.49-.02l2.06-.99c.21-.1.35-.32.35-.56V2.64a.63.63 0 0
  0-.35-.56l-2.06-1a.62.62 0 0 0-.71.13L3.94 4.8 2.22 3.5a.42.42 0 0 0-.53.02l-.55.5a.42.42 0 0 0 0 .62L2.62 6 1.14 7.36a.42.42 0 0 0 0
  .61l.55.5c.15.14.37.15.53.03l1.72-1.3 3.94 3.59c.06.06.13.1.21.14Zm.4-7.2L5.51 6l3 2.27V3.73Z"
										fill="#fff"
									></path>
								</mask>
								<g mask="url(#b)">
									<path
										d="m10.64 2.08-2.06-1a.62.62 0 0 0-.7.13L1.12 7.36a.42.42 0 0 0 0 .61l.55.5c.15.14.37.15.53.03l8.12-6.17c.28-.2.67 0
  .67.33v-.02a.63.63 0 0 0-.36-.56Z"
										fill="#0065A9"
									></path>
									<g filter="url(#c)">
										<path
											d="m10.64 9.92-2.06.99a.62.62 0 0 1-.7-.12L1.12 4.64a.42.42 0 0 1 0-.62l.55-.5a.42.42 0 0 1 .53-.02l8.12
  6.16c.28.2.67.01.67-.33v.03c0 .24-.14.45-.36.56Z"
											fill="#007ACC"
										></path>
									</g>
									<g filter="url(#d)">
										<path
											d="M8.59 10.91a.62.62 0 0 1-.71-.12c.23.23.62.07.62-.26V1.46c0-.32-.4-.48-.63-.25a.62.62 0 0 1
  .72-.12l2.06.99c.21.1.35.32.35.56v6.72c0 .24-.14.46-.35.56l-2.06.99Z"
											fill="#1F9CF0"
										></path>
									</g>
									<path
										fillRule="evenodd"
										clipRule="evenodd"
										d="M8.08 10.93c.16.06.34.06.5-.02l2.06-.99c.21-.1.35-.32.35-.56V2.64a.63.63 0 0
  0-.35-.56l-2.06-1a.62.62 0 0 0-.71.13L3.93 4.8 2.2 3.5a.42.42 0 0 0-.53.02l-.55.5a.42.42 0 0 0 0 .62L2.62 6l-1.5 1.36a.42.42 0 0 0 0
  .61l.56.5c.15.14.37.15.53.03l1.72-1.3 3.94 3.59c.06.06.13.1.21.14Zm.41-7.2L5.5 6l3 2.27V3.73Z"
										fill="url(#e)"
										style={{ mixBlendMode: 'overlay' }}
										opacity=".25"
									></path>
								</g>
							</g>
							<defs>
								<filter
									id="c"
									x="-8.27"
									y="-5.85"
									width="28.53"
									height="26.07"
									filterUnits="userSpaceOnUse"
									colorInterpolationFilters="sRGB"
								>
									<feFlood floodOpacity="0" result="BackgroundImageFix"></feFlood>
									<feColorMatrix
										in="SourceAlpha"
										values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
										result="hardAlpha"
									></feColorMatrix>
									<feOffset></feOffset>
									<feGaussianBlur stdDeviation="4.63"></feGaussianBlur>
									<feColorMatrix values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"></feColorMatrix>
									<feBlend mode="overlay" in2="BackgroundImageFix" result="effect1_dropShadow_640_684"></feBlend>
									<feBlend in="SourceGraphic" in2="effect1_dropShadow_640_684" result="shape"></feBlend>
								</filter>
								<filter
									id="d"
									x="-1.38"
									y="-8.24"
									width="21.64"
									height="28.46"
									filterUnits="userSpaceOnUse"
									colorInterpolationFilters="sRGB"
								>
									<feFlood floodOpacity="0" result="BackgroundImageFix"></feFlood>
									<feColorMatrix
										in="SourceAlpha"
										values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
										result="hardAlpha"
									></feColorMatrix>
									<feOffset></feOffset>
									<feGaussianBlur stdDeviation="4.63"></feGaussianBlur>
									<feColorMatrix values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"></feColorMatrix>
									<feBlend mode="overlay" in2="BackgroundImageFix" result="effect1_dropShadow_640_684"></feBlend>
									<feBlend in="SourceGraphic" in2="effect1_dropShadow_640_684" result="shape"></feBlend>
								</filter>
								<linearGradient id="e" x1="5.99" y1="1.02" x2="5.99" y2="10.97" gradientUnits="userSpaceOnUse">
									<stop stopColor="#fff"></stop>
									<stop offset="1" stopColor="#fff" stopOpacity="0"></stop>
								</linearGradient>
								<clipPath id="a">
									<path fill="#fff" transform="translate(1 1)" d="M0 0h10v10H0z"></path>
								</clipPath>
							</defs>
						</svg>
						<span className="text-sm font-medium">Add to VS Code</span>
					</a>
				),
			},
			{
				type: 'text',
				content: 'Click to install the MCP Server within VS Code.',
			},
		],
		manualConfig: {
			title: 'Manual Configuration / Using a READ HF_TOKEN instead of OAuth:',
			steps: [
				{
					type: 'text',
					content: (
						<span>
							Add to your VS Code <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">settings.json</code>{' '}
							file:
						</span>
					),
				},
				{
					type: 'code',
					content: `{
  "servers": {
    "huggingface": {
      "url": "https://huggingface.co/mcp",
      "headers": {
        "Authorization": "Bearer <HF_TOKEN>"
      }
    }
  }
}`,
					copyable: true,
				},
				{
					type: 'text',
					content: (
						<span>
							Replace <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">&lt;HF_TOKEN&gt;</code> with your
							Hugging Face API token.
						</span>
					),
				},
			],
		},
	},
	{
		id: 'cursor',
		name: 'Cursor',
		icon: (
			<svg
				className="h-5 w-5"
				width="1em"
				height="1em"
				viewBox="0 0 12 12"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<defs>
					<linearGradient
						id="paint0_linear_640_687"
						x1="5.99601"
						y1="5.99219"
						x2="5.99601"
						y2="11.3473"
						gradientUnits="userSpaceOnUse"
					>
						<stop className="stop-color-black dark:stop-color-white" offset="0.16" stopOpacity="0.39"></stop>
						<stop className="stop-color-black dark:stop-color-white" offset="0.658" stopOpacity="0.8"></stop>
					</linearGradient>
					<linearGradient
						id="paint1_linear_640_687"
						x1="10.6523"
						y1="3.3347"
						x2="6"
						y2="6.06268"
						gradientUnits="userSpaceOnUse"
					>
						<stop className="stop-color-black dark:stop-color-white" offset="0.182" stopOpacity="0.31"></stop>
						<stop className="stop-color-black dark:stop-color-white" offset="0.715" stopOpacity="0"></stop>
					</linearGradient>
					<linearGradient
						id="paint2_linear_640_687"
						x1="5.99601"
						y1="0.640625"
						x2="1.34375"
						y2="8.6733"
						gradientUnits="userSpaceOnUse"
					>
						<stop className="stop-color-black dark:stop-color-white" stopOpacity="0.6"></stop>
						<stop className="stop-color-black dark:stop-color-white" offset="0.667" stopOpacity="0.22"></stop>
					</linearGradient>
				</defs>
				<path
					d="M5.99601 11.3473L10.6483 8.66975L5.99601 5.99219L1.34375 8.66975L5.99601 11.3473Z"
					fill="url(#paint0_linear_640_687)"
				></path>
				<path d="M10.6523 8.6733V3.31818L6 0.640625V5.99574L10.6523 8.6733Z" fill="url(#paint1_linear_640_687)"></path>
				<path
					d="M5.99601 0.640625L1.34375 3.31818V8.6733L5.99601 5.99574V0.640625Z"
					fill="url(#paint2_linear_640_687)"
				></path>
				<path
					className="fill-gray-500 dark:fill-gray-400"
					d="M10.6523 3.32031L6 11.353V5.99787L10.6523 3.32031Z"
				></path>
				<path
					className="fill-black dark:fill-white"
					d="M10.6483 3.32031L5.99601 5.99787L1.34375 3.32031H10.6483Z"
				></path>
			</svg>
		),
		//		description: 'Use with Cursor AI editor',
		instructions: [
			{
				type: 'text',
				content: (
					<a
						href="https://cursor.com/en/install-mcp?name=huggingface&config=eyJ1cmwiOiJodHRwczovL2h1Z2dpbmdmYWNlLmNvL21jcD9sb2dpbiJ9"
						target="_blank"
						rel="noopener noreferrer"
						className="inline-block border border-border rounded-lg p-2 hover:bg-accent/10 transition-colors duration-200"
					>
						<img
							src="https://cursor.com/deeplink/mcp-install-light.svg"
							alt="Add huggingface MCP server to Cursor"
							height="32"
							className="hover:scale-105 transition-transform duration-200"
						/>
					</a>
				),
			},
			{
				type: 'text',
				content: 'Click to install the MCP Server within Cursor.',
			},
		],
		manualConfig: {
			title: 'Manual Configuration / Using a READ HF_TOKEN instead of OAuth:',
			steps: [
				{
					type: 'text',
					content: (
						<span>
							Edit your Cursor <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">mcp.json</code>{' '}
							configuration file to add the Hugging Face MCP server:
						</span>
					),
				},
				{
					type: 'code',
					content: `{
  "mcpServers": {
    "huggingface": {
      "url": "https://huggingface.co/mcp",
      "headers": {
        "Authorization": "Bearer <HF_TOKEN>"
      }
    }
  }
}`,
					copyable: true,
				},
				{
					type: 'text',
					content: (
						<span>
							Replace <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">&lt;HF_TOKEN&gt;</code> with your
							Hugging Face API Token.
						</span>
					),
				},
			],
		},
	},
	{
		id: 'lm-studio',
		name: 'LM Studio',
		icon: (
			<svg
				className="h-5 w-5"
				xmlns="http://www.w3.org/2000/svg"
				xmlnsXlink="http://www.w3.org/1999/xlink"
				aria-hidden="true"
				focusable="false"
				role="img"
				width="1em"
				height="1em"
				preserveAspectRatio="xMidYMid meet"
				viewBox="0 0 24 24"
			>
				<path
					fill="url(#icon-lm-studio-a)"
					d="M19.337 0H4.663A4.663 4.663 0 0 0 0 4.663v14.674A4.663 4.663 0 0 0 4.663 24h14.674A4.663 4.663 0 0 0 24 19.337V4.663A4.663 4.663 0 0 0 19.337 0"
				></path>
				<g fill="#fff" opacity=".266">
					<path d="M15.803 4.35H7.418a1 1 0 0 0 0 2h8.385a1 1 0 0 0 0-2M19.928 7.063h-8.385a1 1 0 0 0 0 2h8.385a1 1 0 0 0 0-2M17.51 9.776H9.125a1 1 0 0 0 0 2h8.385a1 1 0 0 0 0-2M14.523 12.632H6.138a1 1 0 0 0 0 2h8.385a1 1 0 0 0 0-2M17.51 15.345H9.125a1 1 0 1 0 0 2h8.385a1 1 0 1 0 0-2M20.497 18.059h-4.829a1 1 0 1 0 0 1.999h4.829a1 1 0 1 0 0-2"></path>
				</g>
				<g fill="#fff" opacity=".845">
					<path d="M12.65 4.345H4.265a1 1 0 0 0 0 2h8.385a1 1 0 0 0 0-2M16.775 7.058H8.39a1 1 0 0 0 0 2h8.385a1 1 0 0 0 0-2M14.357 9.771H5.972a1 1 0 0 0 0 2h8.385a1 1 0 0 0 0-2M11.37 12.627H2.985a1 1 0 1 0 0 2h8.385a1 1 0 0 0 0-2M14.357 15.34H5.972a1 1 0 1 0 0 2h8.385a1 1 0 0 0 0-2M17.344 18.054h-4.828a1 1 0 1 0 0 1.999h4.828a1 1 0 1 0 0-2"></path>
				</g>
				<defs>
					<linearGradient
						id="icon-lm-studio-a"
						x1="78.731"
						x2="2229.6"
						y1="0"
						y2="2218.01"
						gradientUnits="userSpaceOnUse"
					>
						<stop stopColor="#6E7EF3"></stop>
						<stop offset="1" stopColor="#4F13BE"></stop>
					</linearGradient>
				</defs>
			</svg>
		),
		//		description: 'Use with LM Studio for local models',
		instructions: [
			{
				type: 'text',
				content: (
					<a
						href="https://lmstudio.ai/install-mcp?name=huggingface&config=eyJ1cmwiOiJodHRwczovL2h1Z2dpbmdmYWNlLmNvL21jcCIsImhlYWRlcnMiOnsiQXV0aG9yaXphdGlvbiI6IkJlYXJlciA8WU9VUl9IRl9UT0tFTj4ifX0%3D"
						target="_blank"
						rel="noopener noreferrer"
						className="inline-block border border-border rounded-lg p-2 hover:bg-accent/10 transition-colors duration-200"
					>
						<img
							src="https://files.lmstudio.ai/deeplink/mcp-install-dark.svg"
							alt="Add MCP Server huggingface to LM Studio"
							className="hover:scale-105 transition-transform duration-200"
						/>
					</a>
				),
			},
			{
				type: 'text',
				content: (
					<span>
						After clicking, replace{' '}
						<code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">&lt;HF_TOKEN&gt;</code> with your READ
						Hugging Face API token.
					</span>
				),
			},
		],
	},
	{
		id: 'gemini-cli',
		name: 'Gemini CLI',
		icon: (
			<svg
				className="h-5 w-5"
				width="1em"
				height="1em"
				viewBox="0 0 548 548"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<g clipPath="url(#clip0_172_122)">
					<rect width="548" height="548" rx="100" fill="#1E1E2E" />
					<path
						d="M449.292 0.0078125C503.925 0.699564 548 45.2028 548 100V448L547.992 449.292C547.3 503.925 502.797 548 448 548H100C44.7715 548 0 503.228 0 448V100C4.09157e-06 45.2032 44.0744 0.700077 98.707 0.0078125L100 0H448L449.292 0.0078125ZM100 32C62.4446 32 32 62.4446 32 100V448C32 485.555 62.4446 516 100 516H448C485.555 516 516 485.555 516 448V100C516 62.4446 485.555 32 448 32H100ZM383.091 238.818V322.455L165.637 427V366.364L343.782 280.637L165.637 194.909V134.273L383.091 238.818Z"
						fill="url(#paint0_linear_172_122)"
					/>
					<path
						d="M449.292 0.0078125C503.925 0.699564 548 45.2028 548 100V448L547.992 449.292C547.3 503.925 502.797 548 448 548H100C44.7715 548 0 503.228 0 448V100C4.09157e-06 45.2032 44.0744 0.700077 98.707 0.0078125L100 0H448L449.292 0.0078125ZM100 32C62.4446 32 32 62.4446 32 100V448C32 485.555 62.4446 516 100 516H448C485.555 516 516 485.555 516 448V100C516 62.4446 485.555 32 448 32H100ZM383.091 238.818V322.455L165.637 427V366.364L343.782 280.637L165.637 194.909V134.273L383.091 238.818Z"
						fill="url(#paint1_linear_172_122)"
					/>
				</g>
				<defs>
					<linearGradient id="paint0_linear_172_122" x1="128" y1="276" x2="421" y2="276" gradientUnits="userSpaceOnUse">
						<stop offset="0.0196292" stopColor="#406AFB" />
						<stop offset="0.226827" stopColor="#078EFB" />
						<stop offset="0.418757" stopColor="#939AFF" />
						<stop offset="0.584515" stopColor="#D698FC" />
						<stop offset="0.774264" stopColor="#FA6178" />
						<stop offset="0.97928" stopColor="#F2554F" />
					</linearGradient>
					<linearGradient id="paint1_linear_172_122" x1="0" y1="276" x2="548" y2="276" gradientUnits="userSpaceOnUse">
						<stop stopColor="#217BFE" />
						<stop offset="0.335283" stopColor="#078EFB" />
						<stop offset="0.7" stopColor="#AC87EB" />
						<stop offset="1" stopColor="#EE4D5D" />
					</linearGradient>
					<clipPath id="clip0_172_122">
						<rect width="548" height="548" rx="100" fill="white" />
					</clipPath>
				</defs>
			</svg>
		),
		//		description: 'Use with Gemini CLI in your terminal',
		instructions: [
			{
				type: 'text',
				content: 'Enter the command below to install in Gemini CLI:',
			},
			{
				type: 'code',
				content: 'gemini mcp add -t http huggingface https://huggingface.co/mcp?login',
				copyable: true,
			},
			{
				type: 'text',
				content: 'Then start Gemini CLI and follow the instructions to complete authentication.',
			},
		],
		actionButtons: [
			{
				type: 'external',
				label: 'Gemini CLI Docs',
				url: 'https://geminicli.com/docs/',
				variant: 'outline',
			},
		],
		manualConfig: {
			title: 'Using the HuggingFace Gemini CLI extension:',
			steps: [
				{
					type: 'text',
					content:
						'The HuggingFace Gemini CLI extension bundles the MCP server with a context file and custom commands, teaching Gemini how to better use all tools.',
				},
				{
					type: 'text',
					content: 'Use the following command to install the extension:',
				},
				{
					type: 'code',
					content: `gemini extensions install https://github.com/huggingface/hf-mcp-server`,
					copyable: true,
				},
				{
					type: 'text',
					content: (
						<span>
							Start Gemini CLI and run{' '}
							<code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">/mcp auth huggingface</code> to
							authenticate.
						</span>
					),
				},
			],
		},
	},
	{
		id: 'claude-code',
		name: 'Claude Code',
		icon: (
			<svg
				className="h-5 w-5"
				width="1em"
				height="1em"
				viewBox="0 0 12 12"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<g clip-path="url(#a)">
					<path
						d="m2.96 7.65 1.97-1.1.03-.1-.03-.05h-.1l-.33-.02-1.12-.03-.97-.04-.95-.06-.24-.05L1 5.91l.02-.15.2-.13.29.02.63.05.95.06.69.04 1.02.11h.16L5 5.84l-.06-.04-.04-.04-.99-.66-1.06-.7-.56-.41-.3-.2-.15-.2-.07-.42.28-.3.36.03.1.02.37.29.8.61 1.03.77.16.12.06-.04v-.03l-.06-.11-.57-1.02-.6-1.04-.27-.43-.07-.26c-.03-.1-.04-.2-.04-.3l.3-.42L3.8 1l.42.06.17.15.26.59.42.93.64 1.26.2.37.1.35.03.1h.07v-.06l.05-.7.1-.88.1-1.12.03-.32.16-.38.3-.2.25.11.2.29-.03.18-.12.77-.23 1.21-.15.81h.09l.1-.1.41-.54.69-.86.3-.34.36-.38.22-.18h.43l.32.47-.14.49-.44.56-.37.47-.53.71-.33.57.03.04h.08l1.2-.26.63-.11.77-.13.35.16.04.16-.14.34-.82.2-.96.2-1.44.33-.01.01.02.03.64.06.28.02h.68l1.25.09.33.22.2.26-.03.2-.5.26-.7-.16-1.59-.38-.54-.13h-.08v.04l.46.45.83.75 1.05.97.05.24-.13.2-.15-.03-.92-.69-.35-.31-.8-.68h-.06v.08l.19.27.98 1.46.05.45-.07.15-.26.09-.28-.05-.57-.8-.59-.9-.47-.82-.06.04-.28 3.02-.13.15-.3.12-.26-.2-.14-.3.14-.62.16-.8.13-.64.12-.79.07-.26v-.02H5.9l-.6.83-.9 1.22-.73.77-.17.07-.3-.15.03-.28.17-.24 1-1.27.6-.78.38-.46v-.06h-.03L2.72 8.73l-.47.06-.2-.19.02-.3.1-.1.8-.55Z"
						fill="#D97757"
					></path>
				</g>
				<defs>
					<clipPath id="a">
						<path fill="#fff" transform="translate(1 1)" d="M0 0h10v10H0z"></path>
					</clipPath>
				</defs>
			</svg>
		),
		//		description: 'Use with Claude Code in your terminal',
		instructions: [
			{
				type: 'text',
				content: 'Enter the command below to install in Claude Code:',
			},
			{
				type: 'code',
				content: 'claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login',
				copyable: true,
			},
			{
				type: 'text',
				content: 'Then start Claude and follow the instructions to complete authentication.',
			},
		],
		actionButtons: [
			{
				type: 'external',
				label: 'Claude Code Docs',
				url: 'https://docs.anthropic.com/en/docs/claude-code',
				variant: 'outline',
			},
		],
		manualConfig: {
			title: 'Using a READ HF_TOKEN instead of OAuth:',
			steps: [
				{
					type: 'text',
					content: 'To use a READ HF_TOKEN instead of OAuth, use the following command:',
				},
				{
					type: 'code',
					content: `claude mcp add hf-mcp-server \\
  -t http https://huggingface.co/mcp \\
  -H "Authorization: Bearer <HF_TOKEN>"`,
					copyable: true,
				},
				{
					type: 'text',
					content: (
						<span>
							Replace <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">&lt;HF_TOKEN&gt;</code> with your
							Hugging Face API token.
						</span>
					),
				},
			],
		},
	},
	{
		id: 'codex-cli',
		name: 'Codex CLI',
		icon: (
			<svg
				className="h-5 w-5"
				xmlns="http://www.w3.org/2000/svg"
				width="1em"
				height="1em"
				fill="none"
				viewBox="0 0 32 32"
			>
				<path
					stroke="#000"
					strokeLinecap="round"
					strokeWidth="2.484"
					d="M22.356 19.797H17.17M9.662 12.29l1.979 3.576a.511.511 0 0 1-.005.504l-1.974 3.409M30.758 16c0 8.15-6.607 14.758-14.758 14.758-8.15 0-14.758-6.607-14.758-14.758C1.242 7.85 7.85 1.242 16 1.242c8.15 0 14.758 6.608 14.758 14.758Z"
				></path>
			</svg>
		),
		instructions: [
			{
				type: 'text',
				content: (
					<a
						href="https://github.com/openai/codex"
						target="_blank"
						rel="noopener noreferrer"
						className="inline-flex items-center space-x-2 text-primary hover:underline cursor-pointer"
					>
						<span>Codex CLI Instructions are at: https://github.com/openai/codex</span>
						<ExternalLink className="h-3 w-3" />
					</a>
				),
			},
			{
				type: 'text',
				content: (
					<span>
						Edit your <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">~/.codex/config.toml</code> and
						include the below:
					</span>
				),
			},
			{
				type: 'code',
				content: `[mcp_servers.huggingface]
command = "npx"
args = ["-y", "mcp-remote@latest", "https://huggingface.co/mcp?login"]`,
				copyable: true,
			},
		],
		actionButtons: [
			{
				type: 'external',
				label: 'Codex CLI Instructions',
				url: 'https://github.com/openai/codex',
				variant: 'outline',
			},
		],
	},
];

export function SettingsCopyPage() {
	const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set());

	// Handler for copying MCP URL
	const handleCopyMcpUrl = async () => {
		const mcpUrl = `https://huggingface.co/mcp?login`;
		try {
			await navigator.clipboard.writeText(mcpUrl);
		} catch (err) {
			console.error('Failed to copy URL:', err);
		}
	};

	// Handler for going to settings (switch to search tab)
	const handleGoToSettings = () => {
		window.open('https://huggingface.co/settings/mcp', '_blank');
	};

	// Handler for toggling client configuration sections
	const toggleClientExpansion = (clientId: string) => {
		setExpandedClients((prev) => {
			const newSet = new Set(prev);
			if (newSet.has(clientId)) {
				newSet.delete(clientId);
			} else {
				newSet.add(clientId);
			}
			return newSet;
		});
	};

	// Handler for action buttons
	const handleActionButton = async (button: ActionButton) => {
		switch (button.type) {
			case 'copy':
				if (button.content) {
					try {
						await navigator.clipboard.writeText(button.content);
					} catch (err) {
						console.error('Failed to copy content:', err);
					}
				}
				break;
			case 'link':
			case 'external':
				if (button.url) {
					window.open(button.url, '_blank');
				}
				break;
			case 'download':
				if (button.url) {
					const link = document.createElement('a');
					link.href = button.url;
					link.download = button.label;
					document.body.appendChild(link);
					link.click();
					document.body.removeChild(link);
				}
				break;
		}
	};

	// Component for rendering instruction steps
	const renderInstructionStep = (step: InstructionStep, index: number) => {
		const baseClasses = 'text-sm';

		switch (step.type) {
			case 'warning':
				return (
					<div key={index} className="flex items-start space-x-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
						<AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
						<div className="text-sm text-yellow-800">{step.content}</div>
					</div>
				);
			case 'info':
				return (
					<div key={index} className="flex items-start space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
						<Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
						<div className="text-sm text-blue-800">{step.content}</div>
					</div>
				);
			case 'code':
				return (
					<div key={index} className="relative group">
						<pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
							<code className="text-foreground font-mono">{step.content}</code>
						</pre>
						{step.copyable && (
							<CopyButton
								content={step.content as string}
								variant="ghost"
								size="sm"
								iconOnly
								className="absolute top-2 right-2 h-6 px-2 text-xs"
							/>
						)}
					</div>
				);
			case 'button':
				return (
					<div key={index} className="flex items-center space-x-3">
						<span className={baseClasses + ' text-muted-foreground flex-grow'}>{step.content}</span>
						{step.button && (
							<Button
								variant={step.button.variant || 'default'}
								size="sm"
								onClick={() => handleActionButton(step.button!)}
								className="ml-auto cursor-pointer"
							>
								{step.button.type === 'external' && <ExternalLink className="h-4 w-4 mr-2" />}
								{step.button.type === 'download' && <Download className="h-4 w-4 mr-2" />}
								{step.button.type === 'copy' && <Copy className="h-4 w-4 mr-2" />}
								{step.button.label}
							</Button>
						)}
					</div>
				);
			default:
				return (
					<div key={index} className={baseClasses + ' text-muted-foreground'}>
						{step.content}
					</div>
				);
		}
	};

	return (
		<div className="min-h-screen bg-background">
			{/* Hero Section with HF Logo */}
			<div className="bg-gradient-to-b from-primary/5 to-background px-8 pt-12 pb-8">
				<div className="max-w-4xl mx-auto text-center">
					<img src={hfLogoWithTitle} alt="Hugging Face" className="h-16 mx-auto mb-8" />
					<h2 className="text-3xl font-bold text-foreground mb-4">Welcome to the Hugging Face MCP Server</h2>
					<p className="text-lg text-muted-foreground max-w-2xl mx-auto">
						Connect assistants to the Hub and thousands of AI Apps
					</p>
				</div>
			</div>

			<div className="px-8 pb-12">
				<div className="max-w-3xl mx-auto">
					{/* Action Buttons Card */}
					<Card>
						<CardHeader className="pb-0">
							<CardTitle className="text-xl font-semibold">Get Started</CardTitle>
						</CardHeader>
						<CardContent className="space-y-6 pt-0">
							{/* Side-by-side layout on larger screens */}
							<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
								{/* Step 1 */}
								<div className="space-y-4">
									<div className="flex items-center space-x-3 mb-4">
										<span className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-lg font-bold">
											1
										</span>
										<span className="text-lg font-medium text-foreground">Setup your Client with this URL:</span>
									</div>

									{/* URL input with embedded copy button */}
									<div className="relative">
										<input
											type="text"
											value="https://huggingface.co/mcp?login"
											readOnly
											className="w-full px-4 py-3 pr-12 text-sm font-mono bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 h-12 cursor-pointer hover:bg-muted/80 transition-colors"
											onClick={handleCopyMcpUrl}
										/>
										<CopyButton
											content="https://huggingface.co/mcp?login"
											variant="secondary"
											size="sm"
											iconOnly
											className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 px-2"
										/>
									</div>
								</div>

								{/* Step 2 */}
								<div className="space-y-4">
									<div className="flex items-center space-x-3 mb-4">
										<span className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-lg font-bold">
											2
										</span>
										<span className="text-lg font-medium text-foreground">Choose your Apps and Tools</span>
									</div>

									<div className="relative">
										<input
											type="text"
											value="Go to MCP Settings"
											readOnly
											className="w-full pl-12 pr-12 py-3 text-sm bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 h-12 cursor-pointer hover:bg-muted/80 transition-colors"
											onClick={handleGoToSettings}
										/>
										<Button
											size="sm"
											onClick={handleGoToSettings}
											className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 px-2 hover:bg-secondary/80 transition-colors cursor-pointer"
											variant="secondary"
										>
											<ExternalLink className="h-4 w-4" />
										</Button>
										<Settings className="absolute left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
									</div>
								</div>
							</div>
						</CardContent>
					</Card>

					<ToolPresetsCard />

					{/* Client Configuration Section */}
					<Card className="mt-8">
						<CardHeader className="pb-0">
							<div className="text-left">
								<CardTitle className="text-xl font-semibold">Detailed Client Setup</CardTitle>
								<CardDescription>Choose your preferred AI client and follow the setup instructions</CardDescription>
							</div>
						</CardHeader>
						<CardContent className="space-y-4 pt-0">
							{CLIENT_CONFIGS.map((client) => {
								const isExpanded = expandedClients.has(client.id);
								return (
									<div key={client.id} className="border border-border rounded-lg">
										{/* Client Header */}
										<button
											onClick={() => toggleClientExpansion(client.id)}
											className="w-full px-4 py-3 flex items-center justify-between hover:bg-accent/50 transition-colors rounded-lg"
										>
											<div className="flex items-center space-x-3">
												<div className="text-primary">{client.icon}</div>
												<div className="text-left">
													<h4 className="font-semibold text-foreground">{client.name}</h4>
													<p className="text-sm text-muted-foreground">{client.description}</p>
												</div>
											</div>
											<div className="text-muted-foreground">
												{isExpanded ? <ChevronDown className="h-6 w-6" /> : <ChevronRight className="h-6 w-6" />}
											</div>
										</button>

										{/* Expanded Content */}
										{isExpanded && (
											<div className="px-4 pb-4 space-y-4 border-t border-border mt-3 pt-4">
												{/* Action Buttons */}
												{client.actionButtons && client.actionButtons.length > 0 && (
													<div className="flex flex-wrap gap-2">
														{client.actionButtons.map((button, index) => (
															<Button
																key={index}
																variant={button.variant || 'default'}
																size="sm"
																onClick={() => handleActionButton(button)}
																className="h-8 cursor-pointer"
															>
																{button.type === 'external' && <ExternalLink className="h-4 w-4 mr-2" />}
																{button.type === 'download' && <Download className="h-4 w-4 mr-2" />}
																{button.type === 'copy' && <Copy className="h-4 w-4 mr-2" />}
																{button.label}
															</Button>
														))}
													</div>
												)}

												{/* Instructions */}
												<div>
													<h5 className="font-semibold text-sm text-foreground mb-2">
														{client.id === 'lm-studio' || client.id === 'cursor' || client.id === 'vscode'
															? 'One Click Install:'
															: 'Instructions:'}
													</h5>
													<div className="space-y-2">
														{client.instructions.map((instruction, index) => {
															if (typeof instruction === 'string') {
																return (
																	<div key={index} className="flex items-start space-x-2">
																		<span className="text-sm text-muted-foreground flex-shrink-0 mt-0.5">
																			{index + 1}.
																		</span>
																		<span className="text-sm text-muted-foreground">{instruction}</span>
																	</div>
																);
															} else {
																return renderInstructionStep(instruction, index);
															}
														})}
													</div>
												</div>

												{/* Configuration Example */}
												{client.configExample && (
													<div className="relative group">
														<div className="flex items-center justify-between mb-2">
															<h5 className="font-semibold text-sm text-foreground">Configuration:</h5>
														</div>
														<pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
															<code className="text-foreground font-mono">{client.configExample}</code>
														</pre>
														<CopyButton
															content={client.configExample!}
															variant="ghost"
															size="sm"
															className="absolute top-2 right-2 h-6 px-2 text-xs"
														/>
													</div>
												)}

												{/* Manual Configuration */}
												{client.manualConfig && (
													<div>
														<h5 className="font-semibold text-sm text-foreground mb-2">{client.manualConfig.title}</h5>
														<div className="space-y-2">
															{client.manualConfig.steps.map((step, index) => renderInstructionStep(step, index))}
														</div>
													</div>
												)}
											</div>
										)}
									</div>
								);
							})}
						</CardContent>
					</Card>

					{/* What is MCP Card - moved to bottom */}
					<Card className="mt-8">
						<CardHeader className="pb-3">
							<CardTitle className="text-xl font-semibold">What is MCP?</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							<p className="text-base text-muted-foreground leading-relaxed">
								The Model Context Protocol (MCP) is an open standard that enables AI assistants to securely connect to
								external data sources and tools.
							</p>
							<p className="text-base text-muted-foreground leading-relaxed">
								The Hugging Face MCP Server provides seamless access to Hugging Face's vast ecosystem of Models,
								Datasets, Research Papers and state-of-the-art AI tools. This server is Open Source, click the link
								below for details of alternative deployment options, to raise issues or suggest a contribution.
							</p>

							{/* Features Grid */}
							<div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
								<div className="flex items-start space-x-3">
									<Search className="h-5 w-5 text-primary mt-0.5" />
									<div>
										<h4 className="font-semibold text-sm text-foreground">Search Models and Datasets</h4>
										<p className="text-sm text-muted-foreground">Discover Models and Trends</p>
									</div>
								</div>
								<div className="flex items-start space-x-3">
									<Rocket className="h-5 w-5 text-primary mt-0.5" />
									<div>
										<h4 className="font-semibold text-sm text-foreground">Discover Spaces</h4>
										<p className="text-sm text-muted-foreground">Add the latest AI Applications</p>
									</div>
								</div>
								<div className="flex items-start space-x-3">
									<svg
										className="h-5 w-5 mt-0.5"
										viewBox="0 0 98 96"
										xmlns="http://www.w3.org/2000/svg"
										fill="currentColor"
									>
										<path
											fillRule="evenodd"
											clipRule="evenodd"
											d="M48.854 0C21.839 0 0 22 0 49.217c0 21.756 13.993 40.172 33.405 46.69 2.427.49 3.316-1.059 3.316-2.362 0-1.141-.08-5.052-.08-9.127-13.59 2.934-16.42-5.867-16.42-5.867-2.184-5.704-5.42-7.17-5.42-7.17-4.448-3.015.324-3.015.324-3.015 4.934.326 7.523 5.052 7.523 5.052 4.367 7.496 11.404 5.378 14.235 4.074.404-3.178 1.699-5.378 3.074-6.6-10.839-1.141-22.243-5.378-22.243-24.283 0-5.378 1.94-9.778 5.014-13.2-.485-1.222-2.184-6.275.486-13.038 0 0 4.125-1.304 13.426 5.052a46.97 46.97 0 0 1 12.214-1.63c4.125 0 8.33.571 12.213 1.63 9.302-6.356 13.427-5.052 13.427-5.052 2.67 6.763.97 11.816.485 13.038 3.155 3.422 5.015 7.822 5.015 13.2 0 18.905-11.404 23.06-22.324 24.283 1.78 1.548 3.316 4.481 3.316 9.126 0 6.6-.08 11.897-.08 13.526 0 1.304.89 2.853 3.316 2.364 19.412-6.52 33.405-24.935 33.405-46.691C97.707 22 75.788 0 48.854 0z"
											fill="#6b7280"
										/>
									</svg>
									<div>
										<h4 className="font-semibold text-sm text-foreground">
											<a
												href="https://github.com/huggingface/hf-mcp-server"
												target="_blank"
												rel="noopener noreferrer"
												className="hover:text-primary hover:underline transition-colors duration-200 inline-flex items-center space-x-1"
											>
												<span>Open Source</span>
												<ExternalLink className="h-3 w-3" />
											</a>
										</h4>
										<p className="text-sm text-muted-foreground">Contribute on GitHub</p>
									</div>
								</div>
							</div>
						</CardContent>
					</Card>
				</div>
			</div>
		</div>
	);
}
