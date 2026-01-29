import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { GradioWidgetApp } from './components/GradioWidgetApp';
import './index.css';

createRoot(document.getElementById('root')!).render(
	<StrictMode>
		<GradioWidgetApp />
	</StrictMode>
);
