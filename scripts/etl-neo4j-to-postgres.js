#!/usr/bin/env node
/**
 * Neo4j → PostgreSQL ETL
 *
 * 把知識圖譜（Artist / Artwork / Institution 與 CREATED / HELD_BY 關係）
 * 匯入 REST API 使用的 PostgreSQL 資料庫（database_schema.sql）。
 *
 * 設計要點：
 * - 冪等：可重複執行。Artwork 以 Neo4j 的 id 屬性（存於 metadata->>'source_id'）
 *   為自然鍵 upsert；Artist / Institution 以 name upsert；collections 以
 *   (artwork_id, institution_id) 唯一。所需的 unique index 由本腳本自行建立。
 * - 多創作者：圖譜中 944 件作品有多位創作者（最多 35 位），但 artworks.artist_id
 *   是單一 FK —— 取第一位，完整名單存 metadata.creators。
 * - 年份：Artwork.date 是自由字串（"ca. 1503"、"1888-1890"、空字串…），
 *   取第一個 4 位數字，範圍外（<-3000 或 >2100）視為無效。
 *
 * 用法：
 *   node scripts/etl-neo4j-to-postgres.js            # 執行
 *   node scripts/etl-neo4j-to-postgres.js --dry-run  # 只讀取與統計，不寫入
 *
 * 連線參數沿用專案慣例，可用環境變數覆蓋：
 *   NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD（預設 bolt://127.0.0.1:7688）
 *   DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD（同 src/database/models.js）
 */

const neo4j = require('neo4j-driver');
const { Pool } = require('pg');
require('dotenv').config();

const DRY_RUN = process.argv.includes('--dry-run');
const BATCH = 500;

const NEO4J_URI = process.env.NEO4J_URI || 'bolt://127.0.0.1:7688';
const NEO4J_USER = process.env.NEO4J_USER || 'neo4j';
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || 'mysecretpassword';

const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'art_history_db',
    password: process.env.DB_PASSWORD || 'password',
    port: process.env.DB_PORT || 5432,
    max: 5
});

const driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD), {
    disableLosslessIntegers: true
});

/** 從自由格式日期字串取出可信的年份，取不出來回傳 null。 */
function parseYear(...candidates) {
    for (const c of candidates) {
        if (c === null || c === undefined) continue;
        const m = String(c).match(/-?\d{4}/);
        if (!m) continue;
        const y = parseInt(m[0], 10);
        if (y >= -3000 && y <= 2100) return y;
    }
    return null;
}

function truncate(s, n) {
    if (s === null || s === undefined) return null;
    const str = String(s);
    return str.length > n ? str.slice(0, n) : str;
}

async function ensureIndexes(client) {
    // 冪等所需的唯一鍵。expression index 上多個 NULL 不互相衝突，安全。
    await client.query('CREATE UNIQUE INDEX IF NOT EXISTS uq_artists_name ON artists (name)');
    await client.query(
        'CREATE UNIQUE INDEX IF NOT EXISTS uq_institutions_name ON institutions (name)'
    );
    await client.query(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_artworks_source_id ON artworks ((metadata->>'source_id'))"
    );
    await client.query(
        'CREATE UNIQUE INDEX IF NOT EXISTS uq_collections_artwork_institution ON collections (artwork_id, institution_id)'
    );
}

async function etlInstitutions(session, client) {
    const result = await session.run(
        'MATCH (i:Institution) WHERE i.name IS NOT NULL RETURN i.name AS name ORDER BY name'
    );
    const names = result.records.map((r) => r.get('name'));
    console.log(`🏛️  Institution 節點: ${names.length}`);
    if (DRY_RUN) return new Map();

    const idByName = new Map();
    for (const name of names) {
        const res = await client.query(
            `INSERT INTO institutions (name, metadata)
             VALUES ($1, $2)
             ON CONFLICT (name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
             RETURNING id`,
            [truncate(name, 300), { source: 'neo4j_etl' }]
        );
        idByName.set(name, res.rows[0].id);
    }
    console.log(`   upsert 完成: ${idByName.size}`);
    return idByName;
}

async function etlArtists(session, client) {
    const result = await session.run(
        `MATCH (a:Artist) WHERE a.name IS NOT NULL
         RETURN a.name AS name, a.source AS source,
                a.birth_year AS birth_year, a.name_tc AS name_tc, a.name_en AS name_en
         ORDER BY name`
    );
    console.log(`🧑‍🎨 Artist 節點（有 name）: ${result.records.length}`);
    if (DRY_RUN) return new Map();

    const idByName = new Map();
    let n = 0;
    for (const r of result.records) {
        const name = r.get('name');
        if (idByName.has(name)) continue; // 圖譜若有同名節點，合併為一筆
        const variants = [r.get('name_tc'), r.get('name_en')].filter(Boolean);
        const res = await client.query(
            `INSERT INTO artists (name, name_variants, birth_year, metadata)
             VALUES ($1, $2, $3, $4)
             ON CONFLICT (name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
             RETURNING id`,
            [
                truncate(name, 255),
                JSON.stringify(variants),
                parseYear(r.get('birth_year')),
                { source: r.get('source') || null, etl: 'neo4j_etl' }
            ]
        );
        idByName.set(name, res.rows[0].id);
        n++;
        if (n % 500 === 0) console.log(`   ...${n}`);
    }
    console.log(`   upsert 完成: ${idByName.size}`);
    return idByName;
}

async function etlArtworks(session, client, artistIdByName, institutionIdByName) {
    const countRes = await session.run('MATCH (w:Artwork) RETURN count(w) AS c');
    const total = countRes.records[0].get('c');
    console.log(`🖼️  Artwork 節點: ${total}`);
    if (DRY_RUN) return { artworks: 0, collections: 0 };

    let done = 0;
    let collections = 0;
    let skipped = 0;

    for (let skip = 0; skip < total; skip += BATCH) {
        const result = await session.run(
            `MATCH (w:Artwork)
             OPTIONAL MATCH (a:Artist)-[:CREATED]->(w)
             OPTIONAL MATCH (w)-[:HELD_BY]->(i:Institution)
             WITH w, collect(DISTINCT a.name) AS creators, collect(DISTINCT i.name) AS holders
             RETURN w, creators, holders
             ORDER BY w.id SKIP $skip LIMIT $limit`,
            { skip: neo4j.int(skip), limit: neo4j.int(BATCH) }
        );

        await client.query('BEGIN');
        try {
            for (const rec of result.records) {
                const w = rec.get('w').properties;
                const creators = rec.get('creators').filter(Boolean);
                const holders = rec.get('holders').filter(Boolean);

                const sourceId = w.id;
                if (!sourceId) {
                    skipped++;
                    continue;
                }

                const title =
                    truncate(w.title, 500) ||
                    truncate(w.title_tc, 500) ||
                    truncate(w.title_en, 500) ||
                    '(untitled)';

                // 取第一位有對應 id 的創作者作為 FK
                let artistId = null;
                for (const c of creators) {
                    if (artistIdByName.has(c)) {
                        artistId = artistIdByName.get(c);
                        break;
                    }
                }

                const metadata = {
                    source_id: sourceId,
                    source: w.source || null,
                    creators,
                    date_raw: w.date || null,
                    department: w.department || null,
                    culture: w.culture || null,
                    period: w.period || null,
                    country: w.country || null,
                    provider: w.provider || null,
                    etl: 'neo4j_etl'
                };

                const res = await client.query(
                    `INSERT INTO artworks
                       (title, artist_id, creation_year, medium, description,
                        style, location, source_urls, metadata)
                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                     ON CONFLICT ((metadata->>'source_id')) DO UPDATE SET
                       title = EXCLUDED.title,
                       artist_id = EXCLUDED.artist_id,
                       creation_year = EXCLUDED.creation_year,
                       medium = EXCLUDED.medium,
                       description = EXCLUDED.description,
                       style = EXCLUDED.style,
                       location = EXCLUDED.location,
                       source_urls = EXCLUDED.source_urls,
                       metadata = EXCLUDED.metadata,
                       updated_at = CURRENT_TIMESTAMP
                     RETURNING id`,
                    [
                        title,
                        artistId,
                        parseYear(w.created_year, w.date),
                        truncate(w.medium, 200),
                        w.description || null,
                        truncate(w.period, 100), // schema 無 period 欄位，以 style 承載
                        truncate(w.country, 300),
                        w.url ? [w.url] : [],
                        metadata
                    ]
                );
                const artworkId = res.rows[0].id;

                // HELD_BY → collections
                for (const h of holders) {
                    const instId = institutionIdByName.get(h);
                    if (!instId) continue;
                    const cres = await client.query(
                        `INSERT INTO collections (artwork_id, institution_id, metadata)
                         VALUES ($1, $2, $3)
                         ON CONFLICT (artwork_id, institution_id) DO NOTHING`,
                        [artworkId, instId, { etl: 'neo4j_etl' }]
                    );
                    collections += cres.rowCount;
                }
                done++;
            }
            await client.query('COMMIT');
        } catch (err) {
            await client.query('ROLLBACK');
            throw err;
        }
        console.log(`   ...${Math.min(skip + BATCH, total)}/${total}`);
    }

    if (skipped) console.log(`   ⚠️ 略過 ${skipped} 筆（無 id 屬性）`);
    return { artworks: done, collections };
}

async function main() {
    console.log(`🚀 Neo4j → PostgreSQL ETL${DRY_RUN ? '（dry-run）' : ''}`);
    console.log(`   Neo4j: ${NEO4J_URI}`);
    console.log(
        `   Postgres: ${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || 5432}/${process.env.DB_NAME || 'art_history_db'}`
    );

    const session = driver.session({ defaultAccessMode: neo4j.session.READ });
    const client = await pool.connect();

    try {
        if (!DRY_RUN) await ensureIndexes(client);

        const institutionIdByName = await etlInstitutions(session, client);
        const artistIdByName = await etlArtists(session, client);
        const { artworks, collections } = await etlArtworks(
            session,
            client,
            artistIdByName,
            institutionIdByName
        );

        if (!DRY_RUN) {
            const counts = await client.query(`
                SELECT
                  (SELECT count(*) FROM artists) AS artists,
                  (SELECT count(*) FROM artworks) AS artworks,
                  (SELECT count(*) FROM institutions) AS institutions,
                  (SELECT count(*) FROM collections) AS collections
            `);
            console.log('\n✅ 完成。PostgreSQL 目前資料量:');
            console.log(`   artists      = ${counts.rows[0].artists}`);
            console.log(`   artworks     = ${counts.rows[0].artworks}  (本次寫入 ${artworks})`);
            console.log(`   institutions = ${counts.rows[0].institutions}`);
            console.log(
                `   collections  = ${counts.rows[0].collections}  (本次新增 ${collections})`
            );
        }
    } finally {
        await session.close();
        await driver.close();
        client.release();
        await pool.end();
    }
}

main().catch((err) => {
    console.error('❌ ETL 失敗:', err.message);
    console.error(err.stack);
    process.exit(1);
});
