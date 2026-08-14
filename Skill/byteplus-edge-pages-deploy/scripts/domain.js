#!/usr/bin/env node
/**
 * BytePlus Edge Pages 域名管理脚本
 * 用法: node domain.js <command> [options]
 *
 * 命令:
 *   add    --project-id <ID> --domain <域名>          添加自定义域名
 *   get    --project-id <ID> --domain <域名>          查看域名详情（含CNAME地址）
 *   list   --project-id <ID>                           列出项目所有域名
 *   verify --project-id <ID> --domain <域名>          验证域名DNS
 *   delete --project-id <ID> --domain <域名>          删除域名
 *   bind   --project-id <ID> --domain <域名>          一键绑定（添加→等CNAME→输出配置指引）
 *
 * API 清单:
 *   AddPagesDomain      添加域名    参数: ProjectID, Domain
 *   GetPagesDomain      查看域名    参数: ProjectID, Domain
 *   ListPagesDomain     列出域名    参数: ProjectID
 *   VerifyPagesDomain   验证域名    参数: ProjectID, Domain
 *   DeletePagesDomain   删除域名    参数: ProjectID, Domain
 */
const { api, sleep } = require('./lib');

// ========== 参数解析 ==========
function parseArgs() {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.log(`用法: node domain.js <command> [options]

命令:
  add    --project-id <ID> --domain <域名>          添加自定义域名
  get    --project-id <ID> --domain <域名>          查看域名详情（含CNAME地址）
  list   --project-id <ID>                           列出项目所有域名
  verify --project-id <ID> --domain <域名>          验证域名DNS
  delete --project-id <ID> --domain <域名>          删除域名
  bind   --project-id <ID> --domain <域名>          一键绑定（添加→等CNAME→输出配置指引）

示例:
  node domain.js bind --project-id p-xxx --domain app.example.com
  node domain.js list --project-id p-xxx
  node domain.js delete --project-id p-xxx --domain app.example.com`);
        process.exit(0);
    }
    const cmd = args[0];
    const opts = {};
    for (let i = 1; i < args.length; i += 2) {
        opts[args[i].replace(/^--/, '')] = args[i + 1];
    }
    return { cmd, opts };
}

function need(opts, keys) {
    for (const k of keys) {
        if (!opts[k]) {
            console.error(`错误: 缺少参数 --${k}`);
            process.exit(1);
        }
    }
}

// ========== 命令实现 ==========

// 添加域名
async function addDomain(projectId, domain) {
    console.log(`正在为项目 ${projectId} 添加域名 ${domain} ...`);
    const res = await api('AddPagesDomain', { ProjectID: projectId, Domain: domain });
    if (res.ResponseMetadata?.Error) {
        const err = res.ResponseMetadata.Error;
        console.error('添加失败:', JSON.stringify(err));
        process.exit(1);
    }
    console.log('  域名已添加，正在生成 CNAME 地址...');
    return res.Result;
}

// 获取域名详情
async function getDomain(projectId, domain) {
    const res = await api('GetPagesDomain', { ProjectID: projectId, Domain: domain });
    if (res.ResponseMetadata?.Error) {
        console.error('查询失败:', JSON.stringify(res.ResponseMetadata.Error));
        process.exit(1);
    }
    return res.Result;
}

// 列出所有域名
async function listDomains(projectId) {
    console.log(`正在列出项目 ${projectId} 的所有域名...\n`);
    const res = await api('ListPagesDomain', { ProjectID: projectId });
    if (res.ResponseMetadata?.Error) {
        console.error('查询失败:', JSON.stringify(res.ResponseMetadata.Error));
        process.exit(1);
    }
    const domains = res.Result?.Data || [];
    if (domains.length === 0) {
        console.log('  该项目尚未绑定自定义域名。');
        console.log('  当前使用 BytePlus 默认预览域名（每 3 小时重置，不可作为稳定地址）。');
        return;
    }
    console.log(`共 ${domains.length} 个域名:\n`);
    for (const d of domains) {
        console.log(`  ${d.Domain}`);
        console.log(`    状态: ${d.Status}`);
        console.log(`    CNAME: ${d.Cname || '(生成中)'}`);
        console.log(`    DNS: ${d.DNSRecord || '(未配置)'}`);
        console.log('');
    }
}

// 验证域名
async function verifyDomain(projectId, domain) {
    console.log(`正在验证域名 ${domain} ...`);
    const res = await api('VerifyPagesDomain', { ProjectID: projectId, Domain: domain });
    if (res.ResponseMetadata?.Error) {
        console.error('验证失败:', JSON.stringify(res.ResponseMetadata.Error));
        process.exit(1);
    }
    return res.Result;
}

// 删除域名
async function deleteDomain(projectId, domain) {
    console.log(`正在删除域名 ${domain} ...`);
    const res = await api('DeletePagesDomain', { ProjectID: projectId, Domain: domain });
    if (res.ResponseMetadata?.Error) {
        console.error('删除失败:', JSON.stringify(res.ResponseMetadata.Error));
        process.exit(1);
    }
    console.log('  域名已删除');
}

// 等待 CNAME 地址生成
async function waitForCname(projectId, domain, maxAttempts = 20) {
    console.log('等待 CNAME 地址生成...');
    for (let i = 0; i < maxAttempts; i++) {
        const d = await getDomain(projectId, domain);
        if (d.Cname) {
            console.log(`  CNAME 地址: ${d.Cname}`);
            return d.Cname;
        }
        process.stdout.write(`  状态: ${d.Status}，等待中... (${i + 1}/${maxAttempts})\r`);
        await sleep(5000);
    }
    console.log('\n  CNAME 地址生成超时，请稍后用 get 命令查询。');
    return null;
}

// 一键绑定流程
async function bindDomain(projectId, domain) {
    console.log('========================================');
    console.log('  自定义域名一键绑定');
    console.log('========================================\n');

    // 步骤1: 添加域名
    console.log('【步骤1/4】添加域名到 BytePlus...');
    try {
        await addDomain(projectId, domain);
    } catch (e) {
        // 可能已添加过，继续
        console.log('  域名可能已存在，继续...');
    }
    console.log('');

    // 步骤2: 等待 CNAME 生成
    console.log('【步骤2/4】获取 CNAME 地址...');
    const cname = await waitForCname(projectId, domain);
    if (!cname) {
        console.log('\n请稍后运行以下命令获取 CNAME:');
        console.log(`  node domain.js get --project-id ${projectId} --domain ${domain}`);
        return;
    }
    console.log('');

    // 步骤3: 输出 DNS 配置指引
    console.log('【步骤3/4】请在你的域名 DNS 管理处添加 CNAME 记录:\n');
    const hostRecord = domain.split('.')[0];
    console.log('  ┌─────────────────────────────────────────────────┐');
    console.log('  │ DNS 配置（以阿里云为例）                         │');
    console.log('  ├────────────┬────────────────────────────────────┤');
    console.log('  │ 记录类型   │ CNAME                              │');
    console.log(`  │ 主机记录   │ ${hostRecord.padEnd(34)}│`);
    console.log(`  │ 记录值     │ ${cname.padEnd(34)}│`);
    console.log('  │ TTL        │ 默认（600秒）                      │');
    console.log('  └────────────┴────────────────────────────────────┘');
    console.log('');
    console.log('  ⚠ 注意:');
    console.log('  - 如果主机记录已存在 A 记录等其他记录，需先删除或修改');
    console.log('  - 不能使用通配符 (*) 记录，每个子域名需单独添加');
    console.log('  - 通配符无效是因为每个项目的 CNAME 地址不同');
    console.log('');

    // 步骤4: 等待用户配置 DNS 后验证
    console.log('【步骤4/4】DNS 配置完成后，运行以下命令验证:');
    console.log(`  node domain.js verify --project-id ${projectId} --domain ${domain}`);
    console.log('');
    console.log('验证通过后，访问 https://' + domain + ' 即可。');
    console.log('');
    console.log('  ⚠ SSL 证书说明:');
    console.log('  - 域名验证通过后，BytePlus 会自动配置 SSL 证书');
    console.log('  - HTTPS 可能需要 5-15 分钟才能正常访问');
    console.log('  - 在此期间 HTTP 可先使用，HTTPS 会随后就绪');
    console.log('  - 如遇 421 Misdirected Request，是 CDN 传播中，等待即可');
    console.log('');
    console.log('========================================');
    console.log('  绑定流程已启动，请按上述步骤操作');
    console.log('========================================');
}

// ========== 主函数 ==========
async function main() {
    const { cmd, opts } = parseArgs();

    switch (cmd) {
        case 'add': {
            need(opts, ['project-id', 'domain']);
            await addDomain(opts['project-id'], opts['domain']);
            break;
        }
        case 'get': {
            need(opts, ['project-id', 'domain']);
            const d = await getDomain(opts['project-id'], opts['domain']);
            console.log('\n域名详情:');
            console.log(JSON.stringify(d, null, 2));
            break;
        }
        case 'list': {
            need(opts, ['project-id']);
            await listDomains(opts['project-id']);
            break;
        }
        case 'verify': {
            need(opts, ['project-id', 'domain']);
            const r = await verifyDomain(opts['project-id'], opts['domain']);
            console.log('验证结果:', JSON.stringify(r, null, 2));
            if (r?.Verified) {
                console.log('\n  域名验证成功！');
            } else if (r?.Error) {
                console.log('\n  验证未通过:', r.Error);
                if (r.Error.includes('already')) {
                    console.log('  域名已验证过，无需重复验证。');
                } else {
                    console.log('  请检查 DNS CNAME 记录是否正确配置。');
                }
            }
            break;
        }
        case 'delete': {
            need(opts, ['project-id', 'domain']);
            await deleteDomain(opts['project-id'], opts['domain']);
            break;
        }
        case 'bind': {
            need(opts, ['project-id', 'domain']);
            await bindDomain(opts['project-id'], opts['domain']);
            break;
        }
        default:
            console.error(`未知命令: ${cmd}`);
            console.error('可用命令: add, get, list, verify, delete, bind');
            process.exit(1);
    }
}

main().catch(e => {
    console.error('执行出错:', e.message);
    process.exit(1);
});
