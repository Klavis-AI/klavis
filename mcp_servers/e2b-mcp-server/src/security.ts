import { logger } from './logger.js';

export class SecurityValidator {
  private static readonly MAX_CODE_LENGTH = 50000; // 50KB
  private static readonly MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  private static readonly MAX_FILENAME_LENGTH = 255;
  
  private static readonly DANGEROUS_PATTERNS = [
    // Network operations
    /import\s+socket/gi,
    /from\s+socket\s+import/gi,
    /urllib\.request/gi,
    /requests\./gi,
    /http\./gi,
    /fetch\(/gi,
    /XMLHttpRequest/gi,
    
    // File system operations outside sandbox
    /\/etc\//gi,
    /\/root\//gi,
    /\/home\/(?!user)/gi,
    /\/usr\/bin/gi,
    /\/sys\//gi,
    /\/proc\//gi,
    
    // Process operations
    /subprocess\./gi,
    /os\.system/gi,
    /exec\(/gi,
    /eval\(/gi,
    /child_process/gi,
    
    // Potential secrets
    /password\s*=\s*["'][^"']+["']/gi,
    /api_key\s*=\s*["'][^"']+["']/gi,
    /secret\s*=\s*["'][^"']+["']/gi,
    /token\s*=\s*["'][^"']+["']/gi,
  ];

  private static readonly ALLOWED_DOMAINS = [
    'pypi.org',
    'npmjs.com',
    'registry.npmjs.org',
    'github.com',
    'api.github.com'
  ];

  static validateCode(code: string, language: 'python' | 'javascript'): { isValid: boolean; reason?: string } {
    // Check code length
    if (code.length > this.MAX_CODE_LENGTH) {
      return { isValid: false, reason: `Code exceeds maximum length of ${this.MAX_CODE_LENGTH} characters` };
    }

    // Check for empty code
    if (!code.trim()) {
      return { isValid: false, reason: 'Code cannot be empty' };
    }

    // Check for dangerous patterns
    for (const pattern of this.DANGEROUS_PATTERNS) {
      if (pattern.test(code)) {
        logger.warn(`Potentially dangerous code pattern detected: ${pattern.source}`);
        // For now, log warning but allow execution - E2B provides sandbox isolation
        // In production, you might want to block certain patterns
      }
    }

    // Language-specific validation
    if (language === 'python') {
      return this.validatePythonCode(code);
    } else if (language === 'javascript') {
      return this.validateJavaScriptCode(code);
    }

    return { isValid: true };
  }

  private static validatePythonCode(code: string): { isValid: boolean; reason?: string } {
    // Check for import restrictions (optional - E2B handles this)
    const restrictedImports = [
      '__import__',
      'importlib',
      'reload'
    ];

    for (const restricted of restrictedImports) {
      if (code.includes(restricted)) {
        logger.warn(`Potentially restricted Python import detected: ${restricted}`);
      }
    }

    return { isValid: true };
  }

  private static validateJavaScriptCode(code: string): { isValid: boolean; reason?: string } {
    // Check for Node.js specific dangerous operations
    const dangerousNodeOps = [
      'require("fs")',
      'require("child_process")',
      'require("os")',
      'require("cluster")',
      'process.exit',
      'process.kill'
    ];

    for (const dangerous of dangerousNodeOps) {
      if (code.includes(dangerous)) {
        logger.warn(`Potentially dangerous Node.js operation detected: ${dangerous}`);
      }
    }

    return { isValid: true };
  }

  static validateFilePath(path: string): { isValid: boolean; reason?: string } {
    // Check path length
    if (path.length > this.MAX_FILENAME_LENGTH) {
      return { isValid: false, reason: `File path exceeds maximum length of ${this.MAX_FILENAME_LENGTH} characters` };
    }

    // Check for empty path
    if (!path.trim()) {
      return { isValid: false, reason: 'File path cannot be empty' };
    }

    // Check for directory traversal
    if (path.includes('..')) {
      return { isValid: false, reason: 'Directory traversal not allowed in file paths' };
    }

    // Check for absolute paths to system directories
    const dangerousPaths = ['/etc', '/root', '/usr', '/sys', '/proc', '/dev'];
    for (const dangerous of dangerousPaths) {
      if (path.startsWith(dangerous)) {
        return { isValid: false, reason: `Access to system directory ${dangerous} is not allowed` };
      }
    }

    // Check for null bytes
    if (path.includes('\0')) {
      return { isValid: false, reason: 'Null bytes not allowed in file paths' };
    }

    return { isValid: true };
  }

  static validateFileContent(content: string): { isValid: boolean; reason?: string } {
    // Check file size
    const contentSize = Buffer.byteLength(content, 'utf8');
    if (contentSize > this.MAX_FILE_SIZE) {
      return { 
        isValid: false, 
        reason: `File content exceeds maximum size of ${this.MAX_FILE_SIZE} bytes` 
      };
    }

    // Check for potential secrets in file content
    const secretPatterns = [
      /-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----/gi,
      /[a-zA-Z0-9+/]{32,}={0,2}/g, // Base64 strings that might be keys
      /sk-[a-zA-Z0-9]{48}/g, // OpenAI API keys
      /ghp_[a-zA-Z0-9]{36}/g, // GitHub personal access tokens
    ];

    for (const pattern of secretPatterns) {
      if (pattern.test(content)) {
        logger.warn('Potential secret detected in file content');
        return { isValid: false, reason: 'File content contains potential secrets' };
      }
    }

    return { isValid: true };
  }

  static validatePackages(packages: string[], language: 'python' | 'javascript'): { isValid: boolean; reason?: string } {
    // Check package count
    if (packages.length === 0) {
      return { isValid: false, reason: 'Package list cannot be empty' };
    }

    if (packages.length > 50) {
      return { isValid: false, reason: 'Too many packages requested (maximum 50)' };
    }

    // Validate individual package names
    for (const pkg of packages) {
      const validation = this.validatePackageName(pkg, language);
      if (!validation.isValid) {
        return validation;
      }
    }

    return { isValid: true };
  }

  private static validatePackageName(packageName: string, language: 'python' | 'javascript'): { isValid: boolean; reason?: string } {
    // Check for empty or invalid package names
    if (!packageName || !packageName.trim()) {
      return { isValid: false, reason: 'Package name cannot be empty' };
    }

    // Check length
    if (packageName.length > 100) {
      return { isValid: false, reason: 'Package name too long' };
    }

    // Basic pattern validation
    if (language === 'python') {
      // Python package names should follow PEP 508
      const pythonPattern = /^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$/;
      if (!pythonPattern.test(packageName)) {
        return { isValid: false, reason: `Invalid Python package name: ${packageName}` };
      }
    } else if (language === 'javascript') {
      // NPM package names
      const npmPattern = /^(@[a-zA-Z0-9-~][a-zA-Z0-9-._~]*\/)?[a-zA-Z0-9-~][a-zA-Z0-9-._~]*$/;
      if (!npmPattern.test(packageName)) {
        return { isValid: false, reason: `Invalid npm package name: ${packageName}` };
      }
    }

    // Check for suspicious packages (you might want to maintain a whitelist/blacklist)
    const suspiciousPatterns = [
      /malware/gi,
      /backdoor/gi,
      /virus/gi,
      /trojan/gi
    ];

    for (const pattern of suspiciousPatterns) {
      if (pattern.test(packageName)) {
        logger.warn(`Suspicious package name detected: ${packageName}`);
        return { isValid: false, reason: `Package name appears suspicious: ${packageName}` };
      }
    }

    return { isValid: true };
  }

  static sanitizeOutput(output: string): string {
    // Remove potential ANSI escape codes
    const ansiEscapePattern = /\x1b\[[0-9;]*[a-zA-Z]/g;
    let sanitized = output.replace(ansiEscapePattern, '');

    // Remove or mask potential sensitive information
    const secretPatterns = [
      { pattern: /sk-[a-zA-Z0-9]{48}/g, replacement: 'sk-***HIDDEN***' },
      { pattern: /ghp_[a-zA-Z0-9]{36}/g, replacement: 'ghp_***HIDDEN***' },
      { pattern: /password\s*[:=]\s*["']([^"']+)["']/gi, replacement: 'password: "***HIDDEN***"' },
      { pattern: /api_key\s*[:=]\s*["']([^"']+)["']/gi, replacement: 'api_key: "***HIDDEN***"' },
    ];

    for (const { pattern, replacement } of secretPatterns) {
      sanitized = sanitized.replace(pattern, replacement);
    }

    return sanitized;
  }

  static logSecurityEvent(event: string, details: any): void {
    logger.warn('Security event:', { event, details, timestamp: new Date().toISOString() });
  }
}