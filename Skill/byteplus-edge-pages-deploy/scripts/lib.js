/**
 * BytePlus Edge Pages 公共库
 * 提供 API 签名、HTTP 请求、文件上传、跨平台 ZIP 打包
 * 仅依赖 Node.js 内置模块，零外部依赖
 */
const crypto = require('crypto');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');

// ========== 配置加载（懒加载，避免 onboard.js save-credentials 时的死循环） ==========
const SCRIPT_DIR = path.dirname(__filename);
const CONFIG_PATH = path.join(SCRIPT_DIR, 'config.json');

let _cachedConfig = null;
function getConfig() {
    if (_cachedConfig) return _cachedConfig;
    if (!fs.existsSync(CONFIG_PATH)) {
        console.error('错误: 未找到 config.json');
        console.error('请复制 config.template.json 为 config.json，并填入 BytePlus 凭证');
        console.error('获取地址: https://console.byteplus.com/iam/keymanage');
        process.exit(1);
    }
    const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
    if (!cfg.access_key || !cfg.secret_key || cfg.access_key.startsWith('YOUR_') || cfg.secret_key.startsWith('YOUR_')) {
        console.error('错误: config.json 中仍是占位符，请填入真实的 BytePlus 凭证');
        console.error('获取地址: https://console.byteplus.com/iam/keymanage');
        process.exit(1);
    }
    _cachedConfig = cfg;
    return cfg;
}

const CT = 'application/json';

// ========== 加密辅助 ==========
function hmacSHA256(key, msg) {
    return crypto.createHmac('sha256', key).update(msg, 'utf8').digest();
}

function getSigningKey(sk, dateStamp, region, service) {
    const kDate = hmacSHA256(Buffer.from(sk, 'utf8'), dateStamp);
    const kRegion = hmacSHA256(kDate, region);
    const kService = hmacSHA256(kRegion, service);
    return hmacSHA256(kService, 'request');
}

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

// ========== HTTP 请求 ==========
function httpRequest(url, method, body, headers, timeout = 60000) {
    return new Promise((resolve, reject) => {
        const u = new URL(url);
        const options = {
            hostname: u.hostname,
            port: 443,
            path: u.pathname + u.search,
            method: method,
            headers: headers,
            timeout: timeout,
        };
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    resolve({ raw: data, statusCode: res.statusCode });
                }
            });
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('请求超时')); });
        if (body) req.write(body);
        req.end();
    });
}

// ========== 文件上传 ==========
function uploadFile(url, data) {
    return new Promise((resolve, reject) => {
        const u = new URL(url);
        const options = {
            hostname: u.hostname,
            port: 443,
            path: u.pathname + u.search,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/zip',
                'Content-Length': data.length,
            },
            timeout: 120000,
        };
        const req = https.request(options, (res) => {
            let respData = '';
            res.on('data', chunk => respData += chunk);
            res.on('end', () => resolve(res.statusCode));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('上传超时')); });
        req.write(data);
        req.end();
    });
}

// ========== HTTP GET (用于验证预览链接) ==========
function httpGet(url, timeout = 30000) {
    return new Promise((resolve) => {
        const u = new URL(url);
        const req = https.request({
            hostname: u.hostname,
            port: 443,
            path: u.pathname + u.search,
            method: 'GET',
            timeout: timeout,
        }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({ statusCode: res.statusCode, body: data, length: data.length }));
        });
        req.on('error', (e) => resolve({ statusCode: 0, error: e.message }));
        req.on('timeout', () => { req.destroy(); resolve({ statusCode: 0, error: 'timeout' }); });
        req.end();
    });
}

// ========== API 调用（带重试） ==========
async function api(action, body = {}, retries = 8) {
    const cfg = getConfig();
    const ak = cfg.access_key;
    const sk = cfg.secret_key;
    const host = cfg.host || 'cdn.byteplusapi.com';
    const region = cfg.region || 'ap-singapore-1';
    const service = (cfg.service || 'CDN').toLowerCase();
    const version = cfg.version || '2021-03-01';

    for (let attempt = 0; attempt < retries; attempt++) {
        try {
            const now = new Date();
            const amzDate = now.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
            const dateStamp = now.toISOString().slice(0, 10).replace(/-/g, '');

            const canonicalQuerystring = `Action=${action}&Version=${version}`;
            const bodyStr = JSON.stringify(body);
            const payloadHash = crypto.createHash('sha256').update(bodyStr, 'utf8').digest('hex');

            const headersToSign = {
                'content-type': CT,
                'host': host,
                'x-date': amzDate,
            };
            const signedHeaders = Object.keys(headersToSign).sort().join(';');
            const canonicalHeaders = Object.keys(headersToSign).sort()
                .map(k => `${k}:${headersToSign[k]}\n`).join('');

            const canonicalRequest = [
                'POST', '/', canonicalQuerystring,
                canonicalHeaders, signedHeaders, payloadHash
            ].join('\n');

            const algorithm = 'HMAC-SHA256';
            const credentialScope = `${dateStamp}/${region}/${service}/request`;
            const stringToSign = [
                algorithm, amzDate, credentialScope,
                crypto.createHash('sha256').update(canonicalRequest, 'utf8').digest('hex')
            ].join('\n');

            const signingKey = getSigningKey(sk, dateStamp, region, service);
            const signature = crypto.createHmac('sha256', signingKey).update(stringToSign, 'utf8').digest('hex');
            const authorization = `${algorithm} Credential=${ak}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;

            const url = `https://${host}/?${canonicalQuerystring}`;
            return await httpRequest(url, 'POST', bodyStr, {
                'Content-Type': CT,
                'Host': host,
                'X-Date': amzDate,
                'Authorization': authorization,
            });
        } catch (e) {
            if (attempt < retries - 1) {
                await sleep(5000);
            } else {
                return {
                    ResponseMetadata: {
                        Error: { Code: 'NetworkError', Message: `${action} 失败（重试 ${retries} 次后）: ${e.message}` }
                    }
                };
            }
        }
    }
}

// ========== 跨平台 ZIP 打包 ==========
// !! 重要: Windows 上必须使用 tar (bsdtar) 而非 Compress-Archive !!
// Compress-Archive 生成的 ZIP 格式与 BytePlus Edge Pages 不兼容，会导致部署后页面返回 404。
// tar 命令在 Windows 10 (1803+) 自带，生成的 ZIP 与 Linux zip 命令格式兼容。
function createZip(dirPath) {
    const tmpZip = path.join(os.tmpdir(), 'byteplus-deploy.zip');
    try { fs.unlinkSync(tmpZip); } catch (e) { }

    if (process.platform === 'win32') {
        // Windows: 优先使用 tar (bsdtar, Windows 10+ 自带)
        try {
            execSync(`tar -a -cf "${tmpZip}" -C "${dirPath}" .`, { stdio: 'pipe' });
        } catch (e) {
            // 降级: PowerShell Compress-Archive (不推荐，可能存在兼容性问题)
            console.error('  警告: tar 命令不可用，降级使用 Compress-Archive');
            console.error('  警告: Compress-Archive 生成的 ZIP 可能导致 BytePlus 部署后返回 404');
            execSync(
                `powershell -Command "Compress-Archive -Path '${dirPath}\\*' -DestinationPath '${tmpZip}' -Force"`,
                { stdio: 'pipe' }
            );
        }
    } else {
        // Mac/Linux: zip 命令
        execSync(`cd "${dirPath}" && zip -r "${tmpZip}" .`, { stdio: 'pipe' });
    }
    return fs.readFileSync(tmpZip);
}

module.exports = { api, uploadFile, sleep, httpRequest, httpGet, createZip, getConfig };
