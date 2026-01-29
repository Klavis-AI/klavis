import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { SettingsCopyPage } from './components/SettingsCopyPage';
import './index.css';

createRoot(document.getElementById('root')!).render(
	<StrictMode>
		<SettingsCopyPage />
	</StrictMode>
);
