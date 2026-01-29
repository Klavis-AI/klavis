import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ToolOption } from './ToolOption';

interface ToolSettings {
	enabled: boolean;
}

interface ToolsCardProps {
	title: string;
	description?: string;
	tools: {
		[toolId: string]: {
			id: string;
			label: string;
			description: string;
			settings: ToolSettings;
		};
	};
	onToolToggle: (toolId: string, checked: boolean) => void;
}

export function ToolsCard({ title, description, tools, onToolToggle }: ToolsCardProps) {
	return (
		<Card className="w-full">
			<CardHeader>
				<CardTitle>{title}</CardTitle>
				<CardDescription>{description}</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="grid grid-cols-2 gap-6 mb-6">
					{Object.entries(tools).map(([toolId, tool]) => (
						<ToolOption
							key={toolId}
							id={tool.id}
							label={tool.label}
							description={tool.description}
							isEnabled={tool.settings.enabled}
							onToggle={(checked) => {
								onToolToggle(tool.id, checked);
							}}
						/>
					))}
				</div>
			</CardContent>
		</Card>
	);
}
