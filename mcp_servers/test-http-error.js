// 测试 HTTPError 的 JSON 序列化
import { STATUS_CODES } from 'http';

class HTTPError extends Error {
	constructor(statusCode, message = STATUS_CODES[statusCode]) {
		super(message);
		this.statusCode = statusCode;
		this.code = `E${String(message).toUpperCase().replace(/\s+/g, '')}`;
	}

	// 添加 toJSON 方法以支持完整的序列化
	toJSON() {
		return {
			name: this.name,
			message: this.message,
			stack: this.stack,
			code: this.code,
			statusCode: this.statusCode
		};
	}
}

// 测试序列化
const error = new HTTPError(404);
console.log('Error object:', error);
console.log('Direct JSON.stringify:', JSON.stringify(error));

// 测试带 toJSON 的版本
class HTTPErrorWithToJSON extends Error {
	constructor(statusCode, message = STATUS_CODES[statusCode]) {
		super(message);
		this.statusCode = statusCode;
		this.code = `E${String(message).toUpperCase().replace(/\s+/g, '')}`;
	}

	toJSON() {
		return {
			name: this.name,
			message: this.message,
			stack: this.stack,
			code: this.code,
			statusCode: this.statusCode
		};
	}
}

const errorWithToJSON = new HTTPErrorWithToJSON(404);
console.log('With toJSON method:', JSON.stringify(errorWithToJSON, null, 2));
