import { useMemo } from 'react';
import { useWidgetProps, useMaxHeight, useTheme } from '../hooks';

interface GradioToolOutput {
	url?: string;
	spaceName?: string;
	[key: string]: unknown;
}

const LOADING_ANIMATIONS = {
	'huggy-pop': {
		url: 'https://chunte-hfba.static.hf.space/images/modern%20Huggies/Huggy%20Pop.gif',
		scale: 'scale-250',
	},
	vibing: {
		url: 'https://chunte-hfba.static.hf.space/images/modern%20Huggies/Vibing%20Huggy.gif',
		scale: 'scale-100',
	},
	doodle: {
		url: 'https://chunte-hfba.static.hf.space/images/modern%20Huggies/Doodle%20Huggy.gif',
		scale: 'scale-90',
	},
};

export function GradioWidgetApp() {
	// Use the new hooks from openai-apps-sdk patterns
	const toolOutput = useWidgetProps<GradioToolOutput>();
	const maxHeight = useMaxHeight();
	const theme = useTheme();

	// Select loading animation with weighted randomness (60% Huggy Pop, 30% Vibing, 10% Doodle)
	const loadingAnimation = useMemo(() => {
		const rand = Math.random() * 100;
		if (rand < 60) return LOADING_ANIMATIONS['huggy-pop'];
		if (rand < 90) return LOADING_ANIMATIONS.vibing;
		return LOADING_ANIMATIONS.doodle;
	}, []);

	// Determine content type based on URL
	const isAudioUrl = toolOutput?.url?.match(/\.wav$/i);
	const isImageUrl = toolOutput?.url?.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i);

	// Calculate container style based on display mode and max height
	const containerStyle = maxHeight
		? { maxHeight: `${maxHeight}px`, minHeight: `${Math.min(maxHeight, 480)}px` }
		: { minHeight: '100vh' };

	// Determine theme-based classes
	const isDark = theme === 'dark';
	const bgGradient = isDark
		? 'bg-gradient-to-b from-neutral-900 to-neutral-800'
		: 'bg-gradient-to-b from-gray-50 to-gray-100';
	const cardBg = isDark ? 'bg-neutral-800' : 'bg-white';
	const textPrimary = isDark ? 'text-gray-100' : 'text-gray-800';
	const textSecondary = isDark ? 'text-gray-400' : 'text-gray-600';
	const textTertiary = isDark ? 'text-gray-500' : 'text-gray-500';

	return (
		<div className={`flex flex-col items-center justify-center p-4 ${bgGradient}`} style={containerStyle}>
			<div className="max-w-2xl w-full">
				{!toolOutput ? (
					<>
						{/* Show random Huggy animation while loading */}
						<div className="flex justify-center mb-6">
							<div className="w-32 h-32 overflow-hidden flex items-center justify-center">
								<img
									src={loadingAnimation.url}
									alt="Hugging Face"
									className={`w-full h-full object-cover ${loadingAnimation.scale}`}
								/>
							</div>
						</div>
						<div className="text-center">
							<p className={textSecondary}>Loading...</p>
						</div>
					</>
				) : isAudioUrl && toolOutput.url ? (
					<div className={`${cardBg} rounded-lg shadow-lg p-6`}>
						<div className="flex items-center gap-3 mb-4">
							<img
								src="https://huggingface.co/datasets/huggingface/brand-assets/resolve/main/hf-logo.svg"
								alt="Hugging Face"
								className="h-8 object-contain"
							/>
							{toolOutput.spaceName ? (
								<a
									href={`https://huggingface.co/spaces/${toolOutput.spaceName}`}
									target="_blank"
									rel="noopener noreferrer"
									className={`text-xl font-semibold ${textPrimary} hover:underline`}
								>
									{toolOutput.spaceName}
								</a>
							) : (
								<h2 className={`text-xl font-semibold ${textPrimary}`}>Audio Player</h2>
							)}
						</div>
						<audio controls className="w-full" src={toolOutput.url}>
							Your browser does not support the audio element.
						</audio>
						<p className={`text-sm ${textTertiary} mt-2 break-all`}>{toolOutput.url}</p>
					</div>
				) : isImageUrl && toolOutput.url ? (
					<div className={`${cardBg} rounded-lg shadow-lg p-6`}>
						<div className="flex items-center gap-3 mb-4">
							<img
								src="https://huggingface.co/datasets/huggingface/brand-assets/resolve/main/hf-logo.svg"
								alt="Hugging Face"
								className="h-8 object-contain"
							/>
							{toolOutput.spaceName ? (
								<a
									href={`https://huggingface.co/spaces/${toolOutput.spaceName}`}
									target="_blank"
									rel="noopener noreferrer"
									className={`text-xl font-semibold ${textPrimary} hover:underline`}
								>
									{toolOutput.spaceName}
								</a>
							) : (
								<h2 className={`text-xl font-semibold ${textPrimary}`}>Image Viewer</h2>
							)}
						</div>
						<div className="flex justify-center items-center">
							<img
								src={toolOutput.url}
								alt="Generated content"
								className="max-w-full h-auto rounded-lg"
								style={{
									maxHeight: maxHeight ? `${maxHeight - 200}px` : '600px',
									objectFit: 'contain',
								}}
								onError={(e) => {
									const target = e.target as HTMLImageElement;
									target.style.display = 'none';
									const errorMsg = target.nextElementSibling;
									if (errorMsg) {
										(errorMsg as HTMLElement).style.display = 'block';
									}
								}}
							/>
							<p className="text-sm text-red-500 mt-2 hidden">Failed to load image</p>
						</div>
						<p className={`text-sm ${textTertiary} mt-4 break-all text-center`}>{toolOutput.url}</p>
					</div>
				) : (
					<div className={`${cardBg} rounded-lg shadow-lg p-6 text-center`}>
						<p className={textSecondary}>
							{toolOutput.url ? 'Content available but no preview available for this type.' : 'No content to display.'}
						</p>
						{toolOutput.url && !isAudioUrl && !isImageUrl && (
							<p className={`text-sm ${textSecondary} mt-2 break-all`}>{toolOutput.url}</p>
						)}
					</div>
				)}
			</div>
		</div>
	);
}
