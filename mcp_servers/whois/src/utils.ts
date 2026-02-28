const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const BLUE = '\x1b[34m';
const RESET = '\x1b[0m';

export function red(text: string) {
  return `${RED}${text}${RESET}`;
}

export function green(text: string) {
  return `${GREEN}${text}${RESET}`;
}

export function yellow(text: string) {
  return `${YELLOW}${text}${RESET}`;
}

export function blue(text: string) {
  return `${BLUE}${text}${RESET}`;
}