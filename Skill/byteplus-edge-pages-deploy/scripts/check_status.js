#!/usr/bin/env node
/**
 * 检查部署状态并获取预览链接
 * 用法: node check_status.js --project-id <项目ID>
 *
 * 增强: 部署成功后自动 HTTP 验证预览链接，检测 404 问题
 */
const { api, sleep, httpGet } = require('./lib');

// 解析参数
const args = process.argv.slice(2);
let PROJECT_ID = '';
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--project-id') PROJECT_ID = args[++i];
}
if (!PROJECT_ID) {
    console.error('用法: node check_status.js --project-id <项目ID>');
    process.exit(1);
}

async function main() {
    console.log(`正在检查项目 ${PROJECT_ID} 的部署状态...\n`);

    for (let attempt = 0; attempt < 10; attempt++) {
        // 获取项目信息
        const projRes = await api('GetPagesProject', { ProjectID: PROJECT_ID });
        const proj = projRes.Result || {};
        const status = proj.Status || 'unknown';
        const previewUrl = proj.PreviewUrl || '';

        // 获取部署信息
        const depRes = await api('ListPagesDeployment', { ProjectID: PROJECT_ID });
        const deployments = depRes.Result?.Data || [];
        const latestDep = deployments[0] || {};
        const depStatus = latestDep.Status || 'unknown';
        const depError = latestDep.DeployConfig?.Error || '';

        console.log(`[第${attempt + 1}/10次] 项目: ${status} | 部署: ${depStatus} | 错误: ${depError || '无'}`);

        if (previewUrl) {
            console.log('\n========================================');
            console.log('  预览链接:');
            console.log('  ' + previewUrl);
            console.log('========================================\n');

            // HTTP 验证预览链接
            console.log('验证链接可访问性...');
            const result = await httpGet(previewUrl);
            if (result.statusCode === 200) {
                console.log(`  HTTP ${result.statusCode} - 链接正常，页面可访问`);
            } else if (result.statusCode === 404) {
                console.log(`  HTTP ${result.statusCode} - 页面返回 404！`);
                console.log('  !! 可能原因:');
                console.log('  !! 1. 使用了 Compress-Archive 创建 ZIP (Windows) -> 改用 tar');
                console.log('  !! 2. 仅通过 CreatePagesProject 部署 -> 需要调用 CreatePagesDeployment');
                console.log('  !! 3. CDN 正在传播中 -> 等待 1-5 分钟后重试');
            } else {
                console.log(`  HTTP ${result.statusCode} - 状态异常`);
            }

            // 提示默认域名失效和自定义域名绑定
            console.log('\n  ⚠ 重要: 默认预览域名每 3 小时失效，不能作为稳定访问地址！');
            console.log('  建议绑定自定义域名以获得永久访问地址:');
            console.log(`  node domain.js bind --project-id ${PROJECT_ID} --domain <你的域名>`);
            return;
        }

        if (depStatus === 'failed') {
            console.log('\n  部署失败:', depError);
            console.log('\n详细信息:');
            console.log(JSON.stringify(projRes, null, 2));
            return;
        }

        if (attempt < 9) {
            console.log('  等待 15 秒...\n');
            await sleep(15000);
        }
    }

    console.log('\n轮询超时，请稍后重试。');
    console.log('最后状态:');
    const projRes = await api('GetPagesProject', { ProjectID: PROJECT_ID });
    console.log(JSON.stringify(projRes, null, 2));
}

main().catch(e => console.error('致命错误:', e));
