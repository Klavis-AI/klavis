import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Checkbox } from './ui/checkbox';
import { Input } from './ui/input';
import { Label } from './ui/label';

interface GradioEndpointsCardProps {
	spaceNames: string[];
	spaceSubdomains: string[];
	enabledSpaces: boolean[];
	onSpaceToolToggle: (index: number, enabled: boolean) => void;
	onSpaceToolNameChange: (index: number, name: string) => void;
	onSpaceToolSubdomainChange: (index: number, subdomain: string) => void;
}

export function GradioEndpointsCard({
	spaceNames,
	spaceSubdomains,
	enabledSpaces,
	onSpaceToolToggle,
	onSpaceToolNameChange,
	onSpaceToolSubdomainChange,
}: GradioEndpointsCardProps) {
	// Always show 3 rows
	const spaceRows = [0, 1, 2];

	return (
		<Card className="w-full">
			<CardHeader>
				<CardTitle>🚀 Gradio Spaces</CardTitle>
				<CardDescription>
					Configure up to 3 Gradio spaces for remote tool access. Edit the name and subdomain fields.
					<span className="font-semibold"> Note: Changes may require reconnecting your MCP client.</span>
				</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="space-y-4">
					{/* Header row */}
					<div className="flex items-center space-x-3 pb-2 border-b">
						<div className="w-6"></div> {/* Checkbox column */}
						<div className="text-sm font-medium min-w-[80px]">Space</div>
						<div className="flex-1 text-sm font-medium">Name</div>
						<div className="flex-1 text-sm font-medium">Subdomain</div>
					</div>

					{spaceRows.map((index) => (
						<div key={index} className="flex items-center space-x-3">
							<Checkbox
								id={`space-tool-${index}`}
								checked={enabledSpaces[index] || false}
								onCheckedChange={(checked) => onSpaceToolToggle(index, checked === true)}
							/>
							<Label htmlFor={`space-tool-${index}`} className="text-sm font-medium min-w-[80px]">
								{index + 1}
							</Label>
							<Input
								placeholder="username/space-name"
								value={spaceNames[index] || ''}
								onChange={(e) => onSpaceToolNameChange(index, e.target.value)}
								className="flex-1 text-sm"
							/>
							<Input
								placeholder="username-space-name"
								value={spaceSubdomains[index] || ''}
								onChange={(e) => onSpaceToolSubdomainChange(index, e.target.value)}
								className="flex-1 text-sm"
							/>
						</div>
					))}
				</div>
			</CardContent>
		</Card>
	);
}
