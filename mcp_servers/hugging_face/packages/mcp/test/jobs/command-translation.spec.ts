import { describe, it, expect } from 'vitest';
import { parseTimeout, parseImageSource, parseCommand, createJobSpec } from '../../src/jobs/commands/utils.js';

describe('Jobs Command Translation', () => {
	describe('parseTimeout', () => {
		it('should parse timeout with seconds', () => {
			expect(parseTimeout('30s')).toBe(30);
			expect(parseTimeout('45s')).toBe(45);
		});

		it('should parse timeout with minutes', () => {
			expect(parseTimeout('5m')).toBe(300);
			expect(parseTimeout('10m')).toBe(600);
		});

		it('should parse timeout with hours', () => {
			expect(parseTimeout('2h')).toBe(7200);
			expect(parseTimeout('1h')).toBe(3600);
		});

		it('should parse timeout with days', () => {
			expect(parseTimeout('1d')).toBe(86400);
		});

		it('should parse plain number as seconds', () => {
			expect(parseTimeout('300')).toBe(300);
			expect(parseTimeout('60')).toBe(60);
		});

		it('should handle decimal values', () => {
			expect(parseTimeout('1.5h')).toBe(5400);
			expect(parseTimeout('2.5m')).toBe(150);
		});

		it('should throw error for invalid format', () => {
			expect(() => parseTimeout('invalid')).toThrow(/Invalid timeout format/);
			expect(() => parseTimeout('xyz')).toThrow(/Invalid timeout format/);
		});

		it('should parse partial numbers (parseInt behavior)', () => {
			// parseInt stops at first non-numeric, so '5x' becomes 5
			expect(parseTimeout('5x')).toBe(5);
			expect(parseTimeout('10abc')).toBe(10);
		});
	});

	describe('parseImageSource', () => {
		it('should detect Docker Hub images', () => {
			const result = parseImageSource('python:3.12');
			expect(result.dockerImage).toBe('python:3.12');
			expect(result.spaceId).toBeUndefined();
		});

		it('should detect HuggingFace Space URLs with https://huggingface.co/', () => {
			const result = parseImageSource('https://huggingface.co/spaces/user/app');
			expect(result.spaceId).toBe('user/app');
			expect(result.dockerImage).toBeUndefined();
		});

		it('should detect HuggingFace Space URLs with https://hf.co/', () => {
			const result = parseImageSource('https://hf.co/spaces/user/app');
			expect(result.spaceId).toBe('user/app');
			expect(result.dockerImage).toBeUndefined();
		});

		it('should detect HuggingFace Space URLs without https prefix', () => {
			const result = parseImageSource('huggingface.co/spaces/user/app');
			expect(result.spaceId).toBe('user/app');
			expect(result.dockerImage).toBeUndefined();
		});

		it('should detect HuggingFace Space URLs with hf.co shorthand', () => {
			const result = parseImageSource('hf.co/spaces/user/app');
			expect(result.spaceId).toBe('user/app');
			expect(result.dockerImage).toBeUndefined();
		});

		it('should treat complex docker images as docker images', () => {
			const result = parseImageSource('ghcr.io/owner/repo:tag');
			expect(result.dockerImage).toBe('ghcr.io/owner/repo:tag');
			expect(result.spaceId).toBeUndefined();
		});
	});

	describe('parseCommand', () => {
		it('should return array commands as-is', () => {
			const result = parseCommand(['python', '-c', 'print("hello")']);
			expect(result.command).toEqual(['python', '-c', 'print("hello")']);
		});

		it('should split simple string commands', () => {
			const result = parseCommand('python script.py');
			expect(result.command).toEqual(['python', 'script.py']);
		});

		it('should handle single word commands', () => {
			const result = parseCommand('ls');
			expect(result.command).toEqual(['ls']);
		});

		it('should handle double-quoted strings', () => {
			const result = parseCommand('python -c "print(\'Hello world!\')"');
			expect(result.command).toEqual(['python', '-c', "print('Hello world!')"]);
		});

		it('should handle single-quoted strings', () => {
			const result = parseCommand("python -c 'print(\"Hello world!\")'");
			expect(result.command).toEqual(['python', '-c', 'print("Hello world!")']);
		});

		it('should handle escaped quotes', () => {
			const result = parseCommand('echo "He said \\"hello\\""');
			expect(result.command).toEqual(['echo', 'He said "hello"']);
		});

		it('should handle mixed quotes and spaces', () => {
			const result = parseCommand('python -c "print(\'hello world\')"');
			expect(result.command).toEqual(['python', '-c', "print('hello world')"]);
		});

		it('should handle multiple quoted arguments', () => {
			const result = parseCommand('cmd "arg one" "arg two" "arg three"');
			expect(result.command).toEqual(['cmd', 'arg one', 'arg two', 'arg three']);
		});

		it('should handle quoted strings with no spaces', () => {
			const result = parseCommand('echo "hello"');
			expect(result.command).toEqual(['echo', 'hello']);
		});

		it('should handle empty quotes', () => {
			const result = parseCommand('echo "" test');
			expect(result.command).toEqual(['echo', '', 'test']);
		});

		it('should handle real-world example from docs', () => {
			const result = parseCommand('python -c "print(\'Hello world!\')"');
			expect(result.command).toEqual(['python', '-c', "print('Hello world!')"]);
		});

		it('should handle commands with multiple spaces', () => {
			const result = parseCommand('python    script.py    --arg');
			expect(result.command).toEqual(['python', 'script.py', '--arg']);
		});

		it('should handle commands with tabs', () => {
			const result = parseCommand('python\tscript.py\t--arg');
			expect(result.command).toEqual(['python', 'script.py', '--arg']);
		});

		it('should handle mixed whitespace', () => {
			const result = parseCommand('cmd  \t arg1\t\t  arg2');
			expect(result.command).toEqual(['cmd', 'arg1', 'arg2']);
		});

		it('should handle backslash escaping (POSIX shell semantics)', () => {
			// In POSIX shells, \n in double quotes is literal, not a newline
			const result = parseCommand('echo "hello\\nworld"');
			expect(result.command).toEqual(['echo', 'hello\\nworld']);
		});

		it('should handle backslash literally in single quotes', () => {
			const result = parseCommand("echo 'hello\\nworld'");
			expect(result.command).toEqual(['echo', 'hello\\nworld']);
		});

		it('should throw error for shell operators', () => {
			expect(() => parseCommand('echo hello | grep world')).toThrow(/Unsupported shell syntax/);
			expect(() => parseCommand('ls && pwd')).toThrow(/Unsupported shell syntax/);
			expect(() => parseCommand('cat file > output.txt')).toThrow(/Unsupported shell syntax/);
		});

		it('should throw error for empty command', () => {
			expect(() => parseCommand('')).toThrow(/Command cannot be empty/);
			expect(() => parseCommand('   ')).toThrow(/Command cannot be empty/);
		});

		it('should handle environment variables as literal references', () => {
			// shell-quote parses $HOME as an env token, which we format as literal string
			// This preserves the variable reference for the job runtime to handle
			const result = parseCommand('echo $HOME');
			expect(result.command).toEqual(['echo', '$HOME']);
		});

		it('should preserve complex environment variable syntax', () => {
			const result = parseCommand('echo ${FOO:-bar} ${BAR?missing}');
			expect(result.command).toEqual(['echo', '${FOO:-bar}', '${BAR?missing}']);
		});

		it('should retain special parameter references', () => {
			const result = parseCommand('echo $$ $1 $@ $* $- $! $_');
			expect(result.command).toEqual(['echo', '$$', '$1', '$@', '$*', '$-', '$!', '$_']);
		});

		it('should treat escaped dollars as literal variables', () => {
			const result = parseCommand('echo \\$FOO "$BAR"');
			expect(result.command).toEqual(['echo', '$FOO', '$BAR']);
		});

		it('should handle multiline Python in array format', () => {
			const result = parseCommand(['python', '-c', 'import sys\nprint("hello")\nprint("world")']);
			expect(result.command).toEqual(['python', '-c', 'import sys\nprint("hello")\nprint("world")']);
		});
	});

	describe('createJobSpec', () => {
		it('should create a basic job spec', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'python -c "print(123)"',
			});

			expect(spec.dockerImage).toBe('python:3.12');
			expect(spec.command).toEqual(['python', '-c', 'print(123)']);
			expect(spec.flavor).toBe('cpu-basic');
		});

		it('should handle Space URLs', () => {
			const spec = createJobSpec({
				image: 'hf.co/spaces/user/app',
				command: 'python run.py',
			});

			expect(spec.spaceId).toBe('user/app');
			expect(spec.dockerImage).toBeUndefined();
		});

		it('should include environment variables', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'python script.py',
				env: { FOO: 'bar', BAZ: 'qux' },
			});

			expect(spec.environment).toEqual({ FOO: 'bar', BAZ: 'qux' });
		});

		it('should include secrets', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'python script.py',
				secrets: { API_KEY: 'secret123' },
			});

			expect(spec.secrets).toEqual({ API_KEY: 'secret123' });
		});

		it('should keep HF_TOKEN literal when no expansion token provided', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'echo $HF_TOKEN',
			});

			expect(spec.command).toEqual(['echo', '$HF_TOKEN']);
		});

		it('should keep command literal even when hfToken provided', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'echo $HF_TOKEN',
				hfToken: 'hf_secret_999',
			});

			expect(spec.command).toEqual(['echo', '$HF_TOKEN']);
		});

		it('should inject HF_TOKEN into secrets when placeholder provided', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'python script.py',
				secrets: { HF_TOKEN: '$HF_TOKEN', OTHER: 'keep' },
				hfToken: 'hf_secret_123',
			});

			expect(spec.secrets).toEqual({ HF_TOKEN: 'hf_secret_123', OTHER: 'keep' });
		});

		it('should inject HF_TOKEN into env when placeholder provided', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'python script.py',
				env: { HF_TOKEN: '${HF_TOKEN}', NAME: 'demo' },
				hfToken: 'hf_env_456',
			});

			expect(spec.environment).toEqual({ HF_TOKEN: 'hf_env_456', NAME: 'demo' });
		});

		it('should leave other env values unchanged', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'python script.py',
				env: { NAME: 'demo' },
				secrets: { API_KEY: 'secret123' },
				hfToken: 'hf_env_456',
			});

			expect(spec.environment).toEqual({ NAME: 'demo' });
			expect(spec.secrets).toEqual({ API_KEY: 'secret123' });
		});

		it('should parse and include timeout', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'python script.py',
				timeout: '5m',
			});

			expect(spec.timeoutSeconds).toBe(300);
		});

		it('should use specified flavor', () => {
			const spec = createJobSpec({
				image: 'python:3.12',
				command: 'python script.py',
				flavor: 'a10g-small',
			});

			expect(spec.flavor).toBe('a10g-small');
		});

		it('should handle array commands', () => {
			const spec = createJobSpec({
				image: 'ubuntu',
				command: ['bash', '-c', 'echo hello'],
			});

			expect(spec.command).toEqual(['bash', '-c', 'echo hello']);
		});
	});
});
