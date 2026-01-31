import { chmod } from 'fs/promises';
import { platform } from 'os';

if (platform() !== 'win32') {
  await chmod('build/index.js', '755');
} 