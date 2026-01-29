'use client';

import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp } from 'lucide-react';

export function createSortableHeader(title: string, align: 'left' | 'right' | 'center' = 'left') {
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	return ({ column }: { column: any }) => {
		const alignClass = align === 'right' ? 'justify-end' : align === 'center' ? 'justify-center' : 'justify-start';
		const sortDirection = column.getIsSorted();

		return (
			<div className={`flex ${alignClass}`}>
				<Button
					variant="ghost"
					onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
					className={`${align === 'right' ? 'ml-auto' : ''} hover:bg-muted/50 h-auto p-0 font-medium text-sm`}
				>
					{title}
					{sortDirection === 'asc' && <ChevronUp className="ml-1 h-3 w-3 text-muted-foreground" />}
					{sortDirection === 'desc' && <ChevronDown className="ml-1 h-3 w-3 text-muted-foreground" />}
				</Button>
			</div>
		);
	};
}
