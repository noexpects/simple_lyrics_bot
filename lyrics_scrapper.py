import requests
from random import choice
import lxml.html

DESKTOP_AGENTS = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']


class LyricsParser():

    def random_headers(self):
        return {'User-Agent': choice(DESKTOP_AGENTS), 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

    def parse_search(self, query):
        search_url = 'https://www.musixmatch.com/search/'
        headers = self.random_headers()
        api = requests.get(search_url+query, headers=headers)
        tree = lxml.html.document_fromstring(api.text)
        best_result_artist = tree.xpath(
            '//*[@id="search-all-results"]/div[1]/div[1]/div[2]/div/ul/li/div/div[2]/div/h3/span/'
            'span/a/text()')
        best_result_title = tree.xpath(
            '//*[@id="search-all-results"]/div[1]/div[1]/div[2]/div/ul/li/div/div[2]/div/h2/a/span'
            '/text()')
        artist_link = tree.xpath('//*[@id="search-all-results"]/div[1]/div[1]/div[2]/div/ul/li/div/div[2]/div/h2/a/@href')
        another_results_artists = tree.xpath('//*[@id="search-all-results"]/div[1]/div[2]//*[@class="artist"]/text()')
        another_results_titles = tree.xpath('//*[@id="search-all-results"]/div[1]/div[2]//*[@class="title"]/span/text()')

        title_href = tree.xpath('//*[@id="search-all-results"]/div[1]/div[2]//*[@class="title"]/@href')

        if len(best_result_title) == 0:
            best_result_artist = tree.xpath(
                '//*[@id="search-all-results"]/div[1]/div[1]/div[2]/ul/li/div/div[2]/div/h2/a/text()')
            if len(best_result_artist) != 0:
                best_result_title = ["Artist"]
                artist_link = tree.xpath(
                    '//*[@id="search-all-results"]/div[1]/div[1]/div[2]/ul/li/div/div[2]/div/h2/a/@href')
        if len(best_result_title) == 0:
            results = "No results found"
        else:
            best_result = [best_result_artist[0]+" - "+best_result_title[0], artist_link[0]]
            final_list = []
            for x in range(len(another_results_artists)):
                dict_href = [another_results_artists[x]+' - '+another_results_titles[x], title_href[x]]
                final_list.append(dict_href)

            results = [best_result, final_list]
        return results

    def parse_text(self, song_list):
        text_url = 'https://www.musixmatch.com/'
        headers = self.random_headers()
        api = requests.get(text_url + song_list[1], headers=headers)
        tree = lxml.html.document_fromstring(api.text)
        song_text = tree.xpath('//*[@id="site"]//*[@class="lyrics__content__ok"]/text()')
        if len(song_text) == 0:
            song_text = tree.xpath('//*[@id="site"]//*[@class="lyrics__content__error"]/text()')

        if len(song_text) == 0:
            song_text = tree.xpath('//*[@id="site"]//*[@class="lyrics__content__warning"]/text()')

        if len(song_text) == 0:
            song_text = 'Sorry, lyrics are not available.'

        return song_text

    def parse_artist(self, artist_link):
        url = 'https://www.musixmatch.com/'
        headers = self.random_headers()
        api = requests.get(url+artist_link, headers=headers)
        tree = lxml.html.document_fromstring(api.text)
        next_page_link = tree.xpath('//*[@id="top-songs"]//*[@class="button page-load-more"]/@href')
        artist_titles = tree.xpath('//*[@id="top-songs"]//*[@class="title"]/span/text()')
        titles_links = tree.xpath('//*[@id="top-songs"]//*[@class="title"]/@href')
        final_list = []

        for x in range(len(artist_titles)):
            dict_href = [artist_titles[x], titles_links[x]]
            final_list.append(dict_href)

        return final_list, next_page_link
