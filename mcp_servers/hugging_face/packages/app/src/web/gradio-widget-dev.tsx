import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { GradioWidgetDevShim } from './components/GradioWidgetDevShim';
import './index.css';

createRoot(document.getElementById('root')!).render(
	<StrictMode>
		<GradioWidgetDevShim />
	</StrictMode>
);
