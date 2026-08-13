#!/usr/bin/env node
/**
 * 新用户引导脚本
 * 用法: node onboard.js <command> [args]
 * 命令: open-browser <url> / save-credentials <ak> <sk> / subscribe-cdn
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { api } = require('./lib');

const SCRIPT_DIR = path.dirname(__filename);
const CONFIG_PATH = path.join(SCRIPT_DIR, 'config.json');
const TEMPLATE_PATH = path.join(SCRIPT_DIR, 'config.template.json');

if (process.argv.length < 3) {
    console.log(`用法: node onboard.js <command> [args]

命令:
  open-browser <url>                在默认浏览器中打开 URL
  save-credentials <ak> <sk>       保存 AK/SK 到 config.json
  subscribe-cdn                     开通 BytePlus CDN 服务`);
    process.exit(0);
}

const CMD = process.argv[2];

function main() {
    switch (CMD) {
        case 'open-browser': {
            const url = process.argv[3];
            if (!url) {
                console.error('错误: 需要 URL 参数');
                process.exit(1);
            }
            console.log(`正在打开: ${url}`);
            try {
                if (process.platform === 'win32') {
                    execSync(`start "" "${url}"`, { stdio: 'pipe' });
                } else if (process.platform === 'darwin') {
                    execSync(`open "${url}"`, { stdio: 'pipe' });
                } else {
                    execSync(`xdg-open "${url}"`, { stdio: 'pipe' });
                }
                console.log('已在浏览器中打开');
            } catch (e) {
                console.log('无法自动打开浏览器，请手动访问:');
                console.log(`  ${url}`);
            }
            break;
        }

        case 'save-credentials': {
            const ak = process.argv[3];
            const sk = process.argv[4];
            if (!ak || !sk) {
                console.error('错误: 需要 access_key 和 secret_key 参数');
                console.error('用法: node onboard.js save-credentials <access_key> <secret_key>');
                process.exit(1);
            }

            // 读取模板或现有配置
            let config;
            if (fs.existsSync(CONFIG_PATH)) {
                config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
            } else if (fs.existsSync(TEMPLATE_PATH)) {
                config = JSON.parse(fs.readFileSync(TEMPLATE_PATH, 'utf8'));
            } else {
                config = {
                    access_key: '', secret_key: '',
                    host: 'cdn.byteplusapi.com',
                    region: 'ap-singapore-1',
                    service: 'CDN',
                    version: '2021-03-01'
                };
            }

            config.access_key = ak;
            config.secret_key = sk;
            fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf8');
            console.log('凭证已保存到 config.json');
            break;
        }

        case 'subscribe-cdn': {
            console.log('正在开通 BytePlus CDN 服务...');
            console.log('区域: overseas, 计费: 按量计费\n');

            (async () => {
                const res = await api('SubscribeCdnService', {
                    Regions: [{ Region: 'overseas', PayType: 'byTraffic95' }]
                });

                if (res.ResponseMetadata?.Error) {
                    const err = res.ResponseMetadata.Error;
                    const msg = err.Message || '';
                    // 已开通不算错误
                    if (msg.includes('already') || msg.includes('已开通') || msg.includes('activated')) {
                        console.log('CDN 服务已开通，无需重复操作');
                    } else {
                        console.error('开通失败:', JSON.stringify(err, null, 2));
                        console.error('\n请手动开通: https://console.byteplus.com/cdn');
                        process.exit(1);
                    }
                } else {
                    console.log('CDN 服务开通成功！');
                    console.log('Pages 平台已就绪，可以开始部署了。');
                }
            })().catch(e => {
                console.error('致命错误:', e);
                process.exit(1);
            });
            break;
        }

        default:
            console.error(`未知命令: ${CMD}`);
            console.error('可用命令: open-browser / save-credentials / subscribe-cdn');
            process.exit(1);
    }
}

main();
