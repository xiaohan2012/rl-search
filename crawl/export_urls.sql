SELECT id,url from webpage where !isnull(crawled_html) and length(crawled_html) != 0;
