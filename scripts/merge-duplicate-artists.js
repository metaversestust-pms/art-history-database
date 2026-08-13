#!/usr/bin/env node
/**
 * 合併 Neo4j 中重複的 Artist 實體。
 *
 * 同一位藝術家常因來源編目慣例不同而產生多個節點，例如
 * 「Vincent van Gogh」/「Gogh, Vincent van」/「Van Gogh, Vincent」。
 * 這會讓圖譜檢索把同一人的作品拆散，也會經 ETL 汙染 PostgreSQL。
 *
 * 用法：
 *   node scripts/merge-duplicate-artists.js --dry-run   # 只輸出計畫
 *   node scripts/merge-duplicate-artists.js             # 實際合併
 *
 * 比對方式：姓名正規化後（去變音符號、去生卒年、去編目角色後綴、
 * 只留字母數字與漢字、token 排序）相同者視為同一人。
 *
 * 刻意不合併的類別：
 * - 佚名佔位符（Unknown / onbekend / anonymous…）：不同的無名作者不是同一人，
 *   合併會製造出一個擁有數十件不相干作品的假實體。
 * - 純生卒年字串（如「1881-1973」）：上游把日期誤存成姓名，合併沒有意義。
 * - 過短的名稱：資訊不足以安全判定為同一人。
 *
 * 保留哪個節點：關係數最多者（減少重接的關係量）。
 * 但顯示名稱另外挑選——關係數最多的節點名稱未必格式最好
 * （例如「Paul Cezanne」比「Paul Cézanne」多一條關係，卻丟失了變音符號）。
 */

const neo4j = require('neo4j-driver');

const DRY_RUN = process.argv.includes('--dry-run');

const NEO4J_URI = process.env.NEO4J_URI || 'bolt://127.0.0.1:7688';
const NEO4J_USER = process.env.NEO4J_USER || 'neo4j';
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || 'mysecretpassword';

const ROLE_SUFFIXES = [
    'auteur du texte',
    'author of the text',
    'editor',
    'publisher',
    'printer',
    'photographer',
    'engraver',
    'illustrator',
    'translator',
    'compiler'
];

const PLACEHOLDER_TOKENS = [
    'unknown',
    'unidentified',
    'anonymous',
    'anonyme',
    'onbekend',
    'unbekannt',
    'desconocido',
    'sconosciuto',
    '佚名',
    '不詳',
    '未知'
];

/** 正規化姓名為比對鍵。 */
function normalize(name) {
    let s = name.normalize('NFKD').replace(/[\u0300-\u036f]/g, ''); // 去組合用變音符號
    s = s.toLowerCase();
    s = s.replace(/\(\s*\d{3,4}\s*-?\s*\d{0,4}\s*\)/g, ' '); // 去 (1853-1890)
    s = s.replace(/[,\s]+\d{4}\s*[-\u2013]\s*\d{0,4}/g, ' '); // 去裸生卒年「, 1928-1987」
    s = s.replace(/^#/, '').replace(/_/g, ' '); // #Name_Rolle 這類來源識別碼
    for (const suf of ROLE_SUFFIXES) s = s.split(suf).join(' ');

    // 用 \p{L} 保留所有語系的字母，只剝除標點與符號。
    // 先前的白名單只留拉丁字母與漢字，會把希臘文／西里爾文姓名整個清空，
    // 導致數十位互不相干的藝術家共用同一個空鍵而被誤判為同一人。
    // 角色限定詞只在括號或底線內才剝除。
    // 早期版本把 artist 當成自由 token 移除，會把編目上的
    // 「Auguste Giraudon's Artist」（替 Giraudon 工作的無名畫師）
    // 誤併到「Auguste Giraudon」本人身上。
    s = s.replace(
        /\((?:artist|kunstler[^)]*|hersteller|zugeschrieben an|attributed to|maker|werkstatt|umkreis)\)/g,
        ' '
    );
    s = s.replace(/(?:^|\s)(?:kunstler in|kunstler|hersteller)(?=\s|$)/g, ' ');

    s = s.replace(/[^\p{L}\p{N}]+/gu, ' ');

    const tokens = s.split(' ').filter((t) => t.length > 1);
    return tokens.sort().join(' ');
}

/** 姓名顯示品質評分，越高越適合當作正規名稱。 */
function nameQuality(name) {
    let score = 0;
    if (/[\r\n]/.test(name)) score -= 100; // 內嵌換行（來源解析殘留）
    const lower = name.toLowerCase();
    if (ROLE_SUFFIXES.some((s) => lower.includes(s))) score -= 50; // 編目角色後綴
    const opens = (name.match(/\(/g) || []).length;
    const closes = (name.match(/\)/g) || []).length;
    if (opens !== closes) score -= 30; // 括號不成對
    if (/\d{4}/.test(name)) score -= 20; // 姓名內嵌年份
    if (/[.,]\s*$/.test(name.trim())) score -= 10; // 尾端標點
    // 保有變音符號／非 ASCII 原文（用碼位判斷，避免在正則裡指涉控制字元）
    if ([...name].some((ch) => ch.codePointAt(0) > 127)) score += 10;
    return score;
}

/**
 * 純編目用語，本身不構成人名。
 * 例：「active 1300-1322」「circa 1450」——去掉年份後只剩這些字，
 * 會讓多個不同年代的條目共用同一個鍵而被誤判為同一人。
 */
const CATALOGUE_WORDS = new Set([
    'active',
    'circa',
    'ca',
    'fl',
    'flourished',
    'century',
    'school',
    'follower',
    'after',
    'style'
]);

/** 這一組是否該合併。 */
function shouldMerge(key) {
    const tokens = key.split(' ');
    if (tokens.every((t) => CATALOGUE_WORDS.has(t))) {
        return { merge: false, reason: '僅由編目用語組成（如 active／circa），非人名' };
    }
    if (PLACEHOLDER_TOKENS.some((p) => tokens.includes(p) || key === p)) {
        return { merge: false, reason: '佚名佔位符（不同無名作者不是同一人）' };
    }
    if (!/[a-z\u4e00-\u9fff]/.test(key)) {
        return { merge: false, reason: '非人名（生卒年被誤存為姓名）' };
    }
    if (key.length <= 3 || tokens.length < 2) {
        return { merge: false, reason: '鍵過短或僅單一詞（單名證據不足以判定為同一人）' };
    }
    return { merge: true, reason: '' };
}

async function main() {
    const driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD));
    const session = driver.session();

    console.log(`🔗 Neo4j: ${NEO4J_URI}${DRY_RUN ? '（dry-run）' : ''}`);

    try {
        const res = await session.run(`
            MATCH (a:Artist)
            OPTIONAL MATCH (a)-[r]->()
            RETURN a.name AS name, elementId(a) AS eid, count(r) AS degree,
                   properties(a) AS props
        `);

        const groups = new Map();
        for (const rec of res.records) {
            const name = rec.get('name');
            if (!name) continue;
            const key = normalize(name);
            if (!key) continue;
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push({
                name,
                eid: rec.get('eid'),
                degree: rec.get('degree').toNumber(),
                props: rec.get('props')
            });
        }

        const plan = [];
        const skipped = [];
        for (const [key, members] of groups) {
            if (members.length < 2) continue;
            const { merge, reason } = shouldMerge(key);
            if (!merge) {
                skipped.push({ key, members, reason });
                continue;
            }
            // 保留關係最多者；名稱另選品質最好的
            const sorted = [...members].sort((a, b) => b.degree - a.degree);
            const best = [...members].sort(
                (a, b) => nameQuality(b.name) - nameQuality(a.name) || b.degree - a.degree
            )[0];
            plan.push({ key, keep: sorted[0], drop: sorted.slice(1), canonicalName: best.name });
        }

        const dropCount = plan.reduce((n, g) => n + g.drop.length, 0);
        console.log(`\n📊 Artist 節點: ${res.records.length}`);
        console.log(`   重複群組: ${plan.length + skipped.length}`);
        console.log(`   將合併  : ${plan.length} 組，移除 ${dropCount} 個節點`);
        console.log(`   排除不動: ${skipped.length} 組`);
        console.log(`   合併後  : ${res.records.length - dropCount} 個 Artist\n`);

        console.log('=== 排除不動 ===');
        for (const s of skipped) {
            console.log(
                `   ${s.members.map((m) => m.name.replace(/\s+/g, ' ').slice(0, 34)).join(' | ')}`
            );
            console.log(`      理由: ${s.reason}`);
        }

        if (DRY_RUN) {
            console.log('\n=== 合併計畫（前 15 組）===');
            for (const g of plan.slice(0, 15)) {
                console.log(`   保留 [${g.keep.degree}條] ${g.canonicalName.replace(/\s+/g, ' ')}`);
                for (const d of g.drop) {
                    console.log(`     <- [${d.degree}條] ${d.name.replace(/\s+/g, ' ')}`);
                }
            }
            console.log('\n（dry-run，未寫入任何資料）');
            return;
        }

        console.log('=== 開始合併 ===');
        let merged = 0;
        for (const g of plan) {
            const dropIds = g.drop.map((d) => d.eid);
            const variants = [...new Set([g.keep.name, ...g.drop.map((d) => d.name)])].filter(
                (n) => n !== g.canonicalName
            );

            await session.executeWrite(async (tx) => {
                // 重接關係（MERGE 避免產生重複邊）
                for (const relType of ['CREATED', 'HAS_TRANSLATION']) {
                    await tx.run(
                        `
                        MATCH (keep:Artist) WHERE elementId(keep) = $keepId
                        MATCH (drop:Artist) WHERE elementId(drop) IN $dropIds
                        MATCH (drop)-[r:${relType}]->(target)
                        MERGE (keep)-[:${relType}]->(target)
                        DELETE r
                        `,
                        { keepId: g.keep.eid, dropIds }
                    );
                }

                // 補齊主節點缺少的屬性（不覆蓋既有值）
                const fillProps = {};
                for (const d of g.drop) {
                    for (const [k, v] of Object.entries(d.props)) {
                        if (k === 'name') continue;
                        if (g.keep.props[k] === undefined && fillProps[k] === undefined) {
                            fillProps[k] = v;
                        }
                    }
                }

                await tx.run(
                    `
                    MATCH (keep:Artist) WHERE elementId(keep) = $keepId
                    SET keep += $fillProps
                    SET keep.name = $canonicalName
                    SET keep.merged_names = $variants
                    `,
                    {
                        keepId: g.keep.eid,
                        fillProps,
                        canonicalName: g.canonicalName,
                        variants
                    }
                );

                // 刪除已被併入的節點（此時應已無關係）
                await tx.run(
                    `
                    MATCH (drop:Artist) WHERE elementId(drop) IN $dropIds
                    DETACH DELETE drop
                    `,
                    { dropIds }
                );
            });

            merged++;
            if (merged % 20 === 0) console.log(`   ...${merged}/${plan.length}`);
        }

        const after = await session.run('MATCH (a:Artist) RETURN count(a) AS c');
        const rels = await session.run('MATCH (:Artist)-[r:CREATED]->() RETURN count(r) AS c');
        console.log(`\n✅ 完成 ${merged} 組合併`);
        console.log(`   Artist 節點: ${after.records[0].get('c').toNumber()}`);
        console.log(`   CREATED 關係: ${rels.records[0].get('c').toNumber()}`);
    } finally {
        await session.close();
        await driver.close();
    }
}

main().catch((err) => {
    console.error('❌ 合併失敗:', err.message);
    console.error(err.stack);
    process.exit(1);
});
