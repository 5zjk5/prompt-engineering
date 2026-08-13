#!/usr/bin/env node
/**
 * BytePlus Edge Pages 部署脚本
 * 用法: node deploy.js --dir <网站目录> [--name <项目名>] [--project-id <已有项目ID>]
 *
 * !! 重要修复说明 !!
 * 原版使用 DeployPagesProject API 部署已有项目，但该 API 对已有项目总是返回
 * "Operation denied: deployment xxx is already in use, no need to deploy"，
 * 不会创建新部署，导致页面返回 404。
 * 修复后使用 CreatePagesDeployment API，该 API 会正确创建新部署。
 *
 * 新建项目流程:
 *   1. CreatePagesProject 创建项目 (必须带 SourceConfig, 会产生初始部署)
 *   2. 等待初始部署完成 (初始部署的内容无法正常访问, 返回 404)
 *   3. 重新上传真实内容并调用 CreatePagesDeployment (产生可正常访问的部署)
 */
const fs = require('fs');
const path = require('path');
const { api, uploadFile, sleep, createZip, httpGet } = require('./lib');

// 解析参数
const args = process.argv.slice(2);
let SITE_DIR = '', PROJECT_NAME = '', PROJECT_ID = '';
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--dir') SITE_DIR = args[++i];
    else if (args[i] === '--name') PROJECT_NAME = args[++i];
    else if (args[i] === '--project-id') PROJECT_ID = args[++i];
}
if (!SITE_DIR) {
    console.error('用法: node deploy.js --dir <网站目录> [--name <项目名>] [--project-id <已有项目ID>]');
    process.exit(1);
}
if (!PROJECT_NAME && !PROJECT_ID) {
    PROJECT_NAME = path.basename(path.resolve(SITE_DIR));
}

// ========== 上传内容并创建部署 (核心函数) ==========
async function uploadAndDeploy(projectId, zipData) {
    // 获取上传信息
    const uploadRes = await api('GetPagesDeploymentUploadInfo', {});
    if (uploadRes.ResponseMetadata?.Error) {
        throw new Error('获取上传信息失败: ' + JSON.stringify(uploadRes.ResponseMetadata.Error));
    }
    const uploadUrl = uploadRes.Result.Url;
    const uploadDir = uploadRes.Result.Directory;
    console.log('  上传目录:', uploadDir);

    // 上传 ZIP
    let uploaded = false;
    for (let i = 0; i < 8; i++) {
        try {
            const status = await uploadFile(uploadUrl, zipData);
            if (status === 200) {
                console.log('  上传成功');
                uploaded = true;
                break;
            }
            console.log(`  [第${i + 1}/8次] HTTP ${status}`);
        } catch (e) {
            console.log(`  [第${i + 1}/8次] ${e.message}`);
        }
        if (i < 7) await sleep(5000);
    }
    if (!uploaded) throw new Error('上传失败，已重试 8 次');

    // 使用 CreatePagesDeployment 创建新部署 (关键修复!)
    const sourceConfig = { Type: 'upload', Directory: uploadDir, AssetsDir: uploadDir };
    console.log('  调用 CreatePagesDeployment...');
    const deployRes = await api('CreatePagesDeployment', { ProjectID: projectId, SourceConfig: sourceConfig });
    if (deployRes.ResponseMetadata?.Error) {
        throw new Error('部署失败: ' + JSON.stringify(deployRes.ResponseMetadata.Error));
    }
    return deployRes.Result?.DeploymentId;
}

async function main() {
    console.log('='.repeat(50));
    console.log('  BytePlus Edge Pages 部署');
    console.log('='.repeat(50));

    // [1] 验证网站目录
    console.log('\n[1] 验证网站目录...');
    if (!fs.existsSync(SITE_DIR)) {
        console.error(`  错误: 目录不存在: ${SITE_DIR}`);
        process.exit(1);
    }
    if (!fs.existsSync(path.join(SITE_DIR, 'index.html'))) {
        console.error(`  错误: 目录中未找到 index.html: ${SITE_DIR}`);
        process.exit(1);
    }
    console.log(`  目录有效: ${SITE_DIR}`);

    // [2] 创建 ZIP
    console.log('\n[2] 创建 ZIP...');
    const zipData = createZip(SITE_DIR);
    console.log(`  ZIP 大小: ${zipData.length} 字节`);

    // [3] 查找或创建项目
    let isNewProject = false;

    if (PROJECT_ID) {
        console.log(`\n[3] 使用指定项目 ${PROJECT_ID}`);
    } else {
        console.log(`\n[3] 查找已有项目 "${PROJECT_NAME}"...`);
        const listRes = await api('ListPagesProject', {});
        if (listRes.ResponseMetadata?.Error) {
            console.error('  列表查询失败:', JSON.stringify(listRes.ResponseMetadata.Error));
            process.exit(1);
        }
        const projects = listRes.Result?.Data || [];
        const existing = projects.find(p => p.Name === PROJECT_NAME);

        if (existing) {
            PROJECT_ID = existing.ProjectId;
            console.log(`  找到已有项目: ${PROJECT_ID}`);
        } else {
            console.log(`  未找到，创建新项目...`);

            // 创建项目时必须带 SourceConfig (API 要求)
            // 先上传一次内容用于创建项目
            const uploadRes = await api('GetPagesDeploymentUploadInfo', {});
            if (uploadRes.ResponseMetadata?.Error) {
                console.error('  错误:', JSON.stringify(uploadRes.ResponseMetadata.Error));
                process.exit(1);
            }
            const initUploadUrl = uploadRes.Result.Url;
            const initUploadDir = uploadRes.Result.Directory;

            // 上传初始 ZIP
            for (let i = 0; i < 8; i++) {
                try {
                    const status = await uploadFile(initUploadUrl, zipData);
                    if (status === 200) break;
                } catch (e) {}
                if (i < 7) await sleep(5000);
            }

            const initSourceConfig = { Type: 'upload', Directory: initUploadDir, AssetsDir: initUploadDir };
            const createRes = await api('CreatePagesProject', {
                Name: PROJECT_NAME,
                Description: PROJECT_NAME,
                SourceConfig: initSourceConfig
            });
            if (createRes.ResponseMetadata?.Error) {
                console.error('  创建失败:', JSON.stringify(createRes.ResponseMetadata.Error));
                process.exit(1);
            }
            PROJECT_ID = createRes.Result?.ProjectId;
            console.log(`  新项目 ID: ${PROJECT_ID}`);
            isNewProject = true;

            // 等待初始部署完成 (CreatePagesProject 会产生初始部署, 但该部署的内容无法正常访问)
            console.log('  等待初始构建完成...');
            for (let i = 0; i < 20; i++) {
                await sleep(10000);
                const projRes = await api('GetPagesProject', { ProjectID: PROJECT_ID });
                const status = projRes.Result?.Status || '';
                process.stdout.write(`\r  等待中... [${i+1}/20] 状态: ${status}   `);
                if (status === 'online' || status === 'failed') break;
            }
            console.log('');

            if (isNewProject) {
                // 初始部署无法正常访问, 需要调用 CreatePagesDeployment 创建真正的部署
                console.log('\n[4] 创建正式部署 (初始部署不可用, 需要重新部署)...');
                const deploymentId = await uploadAndDeploy(PROJECT_ID, zipData);
                console.log(`  部署成功！Deployment ID: ${deploymentId}`);
            }
        }
    }

    // [5] 对已有项目创建新部署
    if (!isNewProject) {
        console.log('\n[4] 上传内容并创建部署...');
        const deploymentId = await uploadAndDeploy(PROJECT_ID, zipData);
        console.log(`  部署成功！Deployment ID: ${deploymentId}`);
    }

    // [6] 等待部署生效并获取预览链接
    console.log('\n[5] 等待部署生效...');
    let previewUrl = '';
    for (let i = 0; i < 12; i++) {
        await sleep(15000);
        const projRes = await api('GetPagesProject', { ProjectID: PROJECT_ID });
        const status = projRes.Result?.Status || '';
        previewUrl = projRes.Result?.PreviewUrl || '';
        const depRes = await api('ListPagesDeployment', { ProjectID: PROJECT_ID });
        const latest = depRes.Result?.Data?.[0] || {};
        console.log(`  [${i+1}/12] 项目: ${status} | 部署: ${latest.Status}`);

        if (status === 'online' && latest.Status === 'success' && previewUrl) {
            break;
        }
    }

    // [7] 验证预览链接可访问 (检测 404)
    if (previewUrl) {
        console.log('\n[6] 验证预览链接...');
        for (let i = 0; i < 4; i++) {
            const result = await httpGet(previewUrl);
            if (result.statusCode === 200) {
                console.log(`  HTTP ${result.statusCode} - 部署成功！`);
                break;
            }
            console.log(`  HTTP ${result.statusCode} - 等待 CDN 传播...`);
            if (i < 3) await sleep(15000);
        }
    }

    console.log('\n========================================');
    console.log('  部署完成！');
    console.log('  项目 ID:', PROJECT_ID);
    if (previewUrl) {
        console.log('  预览链接:');
        console.log('  ' + previewUrl);
    }
    console.log('========================================');
}

main().catch(e => {
    console.error('致命错误:', e);
    process.exit(1);
});
