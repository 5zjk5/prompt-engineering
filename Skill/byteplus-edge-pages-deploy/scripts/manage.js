#!/usr/bin/env node
/**
 * 项目管理脚本
 * 用法: node manage.js <command> [--project-id <ID>]
 * 命令: list / get / deployments / offline / delete
 */
const { api } = require('./lib');

// 解析参数
const args = process.argv.slice(2);
if (args.length === 0) {
    console.log(`用法: node manage.js <command> [--project-id <ID>]

命令:
  list                        列出所有项目
  get       --project-id ID   查看项目详情
  deployments --project-id ID 查看部署历史
  offline   --project-id ID   下线项目
  delete    --project-id ID   删除项目`);
    process.exit(0);
}

const CMD = args[0];
let PROJECT_ID = '';
for (let i = 1; i < args.length; i++) {
    if (args[i] === '--project-id') PROJECT_ID = args[++i];
}

function needProjectId() {
    if (!PROJECT_ID) {
        console.error('错误: 需要 --project-id 参数');
        process.exit(1);
    }
}

async function main() {
    switch (CMD) {
        case 'list': {
            console.log('正在列出所有项目...\n');
            const res = await api('ListPagesProject', {});
            if (res.ResponseMetadata?.Error) {
                console.error('错误:', JSON.stringify(res.ResponseMetadata.Error));
                process.exit(1);
            }
            const projects = res.Result?.Data || [];
            if (projects.length === 0) {
                console.log('  暂无项目');
                return;
            }
            console.log(`共 ${projects.length} 个项目:\n`);
            for (const p of projects) {
                console.log(`  ${p.ProjectId}  ${p.Name}  状态: ${p.Status}  ${p.PreviewUrl ? 'URL: ' + p.PreviewUrl : ''}`);
            }
            break;
        }

        case 'get': {
            needProjectId();
            console.log(`正在获取项目 ${PROJECT_ID} 详情...\n`);
            const res = await api('GetPagesProject', { ProjectID: PROJECT_ID });
            if (res.ResponseMetadata?.Error) {
                console.error('错误:', JSON.stringify(res.ResponseMetadata.Error));
                process.exit(1);
            }
            const p = res.Result || {};
            console.log(`  项目 ID: ${p.ProjectId || PROJECT_ID}`);
            console.log(`  名称: ${p.Name || '-'}`);
            console.log(`  状态: ${p.Status || '-'}`);
            console.log(`  预览链接: ${p.PreviewUrl || '-'}`);
            console.log(`  创建时间: ${p.CreateTime || '-'}`);
            break;
        }

        case 'deployments': {
            needProjectId();
            console.log(`正在获取项目 ${PROJECT_ID} 部署历史...\n`);
            const res = await api('ListPagesDeployment', { ProjectID: PROJECT_ID });
            if (res.ResponseMetadata?.Error) {
                console.error('错误:', JSON.stringify(res.ResponseMetadata.Error));
                process.exit(1);
            }
            const deps = res.Result?.Data || [];
            if (deps.length === 0) {
                console.log('  暂无部署记录');
                return;
            }
            console.log(`共 ${deps.length} 条部署记录:\n`);
            for (const d of deps) {
                console.log(`  ${d.DeploymentId}  状态: ${d.Status}  时间: ${d.CreateTime || '-'}`);
                if (d.DeployConfig?.Error) {
                    console.log(`    错误: ${d.DeployConfig.Error}`);
                }
            }
            break;
        }

        case 'offline': {
            needProjectId();
            console.log(`正在下线项目 ${PROJECT_ID}...`);
            const res = await api('OfflinePagesProject', { ProjectID: PROJECT_ID });
            if (res.ResponseMetadata?.Error) {
                console.error('错误:', JSON.stringify(res.ResponseMetadata.Error));
                process.exit(1);
            }
            console.log('  项目已下线');
            break;
        }

        case 'delete': {
            needProjectId();
            console.log(`正在删除项目 ${PROJECT_ID}...`);
            const res = await api('DeletePagesProject', { ProjectID: PROJECT_ID });
            if (res.ResponseMetadata?.Error) {
                console.error('错误:', JSON.stringify(res.ResponseMetadata.Error));
                process.exit(1);
            }
            console.log('  项目已删除');
            break;
        }

        default:
            console.error(`未知命令: ${CMD}`);
            console.error('可用命令: list / get / deployments / offline / delete');
            process.exit(1);
    }
}

main().catch(e => console.error('致命错误:', e));
