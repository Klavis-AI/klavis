import { Checkbox } from './ui/checkbox';

interface ToolOptionProps {
	id: string;
	label: string;
	description: string;
	isEnabled: boolean;
	onToggle: (checked: boolean) => void;
}

export function ToolOption({ id, label, description, isEnabled, onToggle }: ToolOptionProps) {
	return (
		<div>
			<div className="items-top flex space-x-2">
				<Checkbox id={id} checked={isEnabled} onCheckedChange={(checked) => onToggle(checked === true)} />
				<div className="grid gap-1.5 leading-none">
					<label
						htmlFor={id}
						className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
					>
						{label}
					</label>
					<p className="text-sm text-muted-foreground">{description}</p>
				</div>
			</div>
		</div>
	);
}
