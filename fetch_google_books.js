const axios = require('axios');
const fs = require('fs');

async function fetchGoogleBooksArt() {
    try {
        console.log('📚 開始爬取Google Books藝術史資料...');

        const queries = [
            '藝術史',
            'art history',
            'renaissance art',
            'impressionism',
            '巴洛克藝術',
            'modern art'
        ];

        const allBooks = [];

        for (const query of queries) {
            try {
                console.log(`🔍 搜索: ${query}`);

                const response = await axios.get(
                    `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(query)}&maxResults=5&langRestrict=zh-TW,en`
                );

                if (response.data.items) {
                    for (const item of response.data.items) {
                        const book = {
                            id: item.id,
                            title: item.volumeInfo.title,
                            authors: item.volumeInfo.authors || [],
                            publisher: item.volumeInfo.publisher,
                            publishedDate: item.volumeInfo.publishedDate,
                            description: item.volumeInfo.description,
                            categories: item.volumeInfo.categories || [],
                            pageCount: item.volumeInfo.pageCount,
                            language: item.volumeInfo.language,
                            previewLink: item.volumeInfo.previewLink,
                            infoLink: item.volumeInfo.infoLink,
                            thumbnail: item.volumeInfo.imageLinks?.thumbnail,
                            source: 'Google Books',
                            searchQuery: query
                        };

                        allBooks.push(book);
                        console.log(`📖 ${book.title} - ${book.authors.join(', ')}`);
                    }
                }

                // 避免頻率限制
                await new Promise((resolve) => setTimeout(resolve, 200));
            } catch (error) {
                console.warn(`⚠️ 查詢 '${query}' 失敗: ${error.message}`);
            }
        }

        // 去重（基於標題和作者）
        const uniqueBooks = [];
        const seen = new Set();

        for (const book of allBooks) {
            const key = `${book.title}_${book.authors.join(',')}`;
            if (!seen.has(key)) {
                seen.add(key);
                uniqueBooks.push(book);
            }
        }

        // 保存資料
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `data/raw/google_books/google_books_art_${timestamp}.json`;

        fs.writeFileSync(filename, JSON.stringify(uniqueBooks, null, 2));

        console.log(`✅ Google Books爬取完成！共收集 ${uniqueBooks.length} 本藝術史書籍`);
        console.log(`📁 資料保存至: ${filename}`);

        return uniqueBooks;
    } catch (error) {
        console.error('❌ Google Books爬取失敗:', error.message);
    }
}

fetchGoogleBooksArt();
