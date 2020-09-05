# -*- coding: utf-8 -*-
import json
import re
import logging

from scrapy.exceptions import CloseSpider
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spiders import Spider

from wsl_spider.items import CourseLoader, OccurrenceLoader


# TODO You can find the key in <a onclick></a> and insert it into JAA104.php to ge full detail of syllabus

def customize_url(url, display_lang, term, school, teaching_lang, keyword, results_per_page, start_page, academics_json):
    display_langs = {'en': "en", 'jp': "jp"}
    terms = {'all': "", 'full_year': "0", 'spring_summer': "1", 'fall_winter': "2", 'others': "9"}
    teaching_langs = {'all': "", 'n/a': "00", 'jp': "01", 'en': "02"}
    # Use dict to represent enum
    results_per_page_dict = {'10': "10", '20': "20", '50': "50", '100': "100"}

    display_lang_param = 'pLng=' + display_langs[display_lang]
    term_param = 'p_gakki=' + terms[term]
    school_param = 'p_gakubu=' + academics_json[school]["param"]
    teaching_lang_param = 'p_gengo=' + teaching_langs[teaching_lang]

    results_per_page_param = 'p_number=' + results_per_page_dict[str(results_per_page)]
    start_page_param = 'p_page=' + str(start_page)

    keyword_param = 'keyword=' + keyword if keyword else ''

    params = ([display_lang_param, term_param, school_param, teaching_lang_param, keyword_param,
               results_per_page_param, start_page_param])

    # Remove empty string from list. If function is None, the identity function is assumed => Remove all false elements
    filtered_params = filter(None, params)
    return url + '&'.join(filtered_params)


class SearchSpider(Spider):
    name = 'search'
    allowed_domains = ['wsl.waseda.jp']
    basic_url = 'https://www.wsl.waseda.jp/syllabus/JAA103.php?'
    target_keywords = ['IPSE', 'English-based Undergraduate Program']
    close_spider_msg = "There are no more urls to scrape. Closing spider."
    reach_lower_bound_year_msg = "Scraped data has reached lower bound year {}."
    reach_empty_page_msg = "Scraper has reached an empty page."

    def __init__(self, *args, **kwargs):
        super(SearchSpider, self).__init__(*args, **kwargs)

        # Change the target semester, school, and other parameters here.
        self.year_str = kwargs.get('academic_year')
        self.year = int(self.year_str)
        self.year_lower_bound = self.year - 1
        self.display_lang = kwargs.get('display_lang')
        self.schools = kwargs.get('schools').split(',')
        self.teaching_lang = kwargs.get('teaching_lang')
        self.search_keyword = kwargs.get('keyword')
        self.mongo_db = kwargs.get('mongo_db')
        self.mongo_col = kwargs.get('mongo_col')
        self.path_for_academics_json = kwargs.get('path_for_academics_json')
        with open(self.path_for_academics_json, encoding='utf-8') as f:
            self.academics_json = json.load(f)

        # Check if we're searching for a target keyword
        # If not, self.keyword is None and scraped items will not contain the keywords field
        self.keyword = self.search_keyword if self.search_keyword in self.target_keywords else None
        # Check if we're searching for a target language
        # Cannot use "" for others because it won't be loaded by scrapy
        self.lang = self.teaching_lang if self.teaching_lang != "all" else "others"

        self.term = 'all'

        if self.display_lang == 'en':
            self.undecided_string = 'undecided'
        elif self.display_lang == 'jp':
            self.undecided_string = '未定'
        else:
            raise Exception("display_lang '%s' is not supported." % self.display_lang)

        self.start_school = self.schools[0]
        self.current_school = self.start_school

        self.results_per_page = 100
        self.start_page = 1
        self.current_page = self.start_page

        start_url = customize_url(self.basic_url, self.display_lang, self.term, self.start_school, self.teaching_lang,
                                  self.search_keyword, self.results_per_page, self.start_page, self.academics_json)
        self.start_urls = [start_url]
        self.current_url = start_url

    def parse(self, response):
        reached_lower_bound_year = False
        sel = Selector(response=response, type="html")
        c_infos = sel.xpath('//table[@class="ct-vh"]/tbody/tr[not(@class="c-vh-title")]')
        reached_empty_page = False if c_infos != [] else True
        for c_info in c_infos:
            year = c_info.xpath('td[1]/text()').extract_first()
            if int(year) <= self.year_lower_bound:
                reached_lower_bound_year = True
            onclick_url = c_info.xpath('td[3]/a/@onclick').extract()

            code = self.correct_nbsp_in_list(c_info.xpath('td[2]/text()').extract())
            title = self.correct_nbsp_in_list(c_info.xpath('td[3]/a/text()').extract())
            instructor = self.correct_nbsp_in_list(c_info.xpath('td[4]/text()').extract())
            school = self.correct_nbsp_in_list(c_info.xpath('td[5]/text()').extract())
            term = self.correct_nbsp_in_list(c_info.xpath('td[6]/text()').extract())

            cl = CourseLoader(selector=c_info)
            cl.add_value(field_name='_id', value=onclick_url)
            cl.add_value(field_name='year', value=year)
            cl.add_value(field_name='keywords', value=self.keyword)
            cl.add_value(field_name='lang', value=self.lang)
            cl.add_value(field_name='code', value=code)
            cl.add_value(field_name='title', value=title)
            cl.add_value(field_name='instructor', value=instructor)
            cl.add_value(field_name='school', value=school)
            cl.add_value(field_name='term', value=term)

            day_periods = c_info.xpath('td[7]/text()').extract()
            locations = c_info.xpath('td[8]/text()').extract()

            # extend locations if it's shorter than day_periods for zip function to match properly.
            # e.g. two day_periods but location is undecided (a single element).
            for i in range(len(day_periods)):
                if i >= len(locations):
                    locations.append(locations[i-1])

            for day_period, location in zip(day_periods, locations):
                ol = OccurrenceLoader()
                day_period_match = re.match(
                    r'(\d{2}:)?(?P<day>[A-Z][a-z]*).(?P<start>\d)?-?(?P<end>\d)', day_period
                )

                if day_period_match is None:
                    day_period_match = re.match(
                        r'(\d{2}:)?(?P<value>.*)', day_period
                    )
                    value = day_period_match.group('value')
                    day = value
                    start_period = value
                    end_period = value
                    start_time = self.period_to_minutes(value)
                    end_time = self.period_to_minutes(value)
                else:
                    day = day_period_match.group('day')
                    start_period = day_period_match.group('start')
                    end_period = day_period_match.group('end')
                    if start_period is None:
                        start_period = end_period
                    start_time = self.period_to_minutes(start_period + 's')
                    end_time = self.period_to_minutes(end_period + 'e')

                ol.add_value(field_name='day', value=day)
                ol.add_value(field_name='start_period', value=start_period)
                ol.add_value(field_name='end_period', value=end_period)
                # ol.add_value(field_name='start_time', value=int(start_time))
                # ol.add_value(field_name='end_time', value=int(end_time))

                location_match = re.match(
                    r'(\d{2}:)?(?P<building>\d+)-(?P<classroom>.*)', location
                )

                if location_match is None:
                    location_match = re.match(
                        r'(\d{2}:)?(?P<value>.*)', location
                    )
                    bldg = '-1'
                    classroom = location_match.group('value')

                else:
                    bldg = location_match.group('building')
                    classroom = location_match.group('classroom')

                ol.add_value(field_name='building', value=bldg)
                ol.add_value(field_name='classroom', value=classroom)
                ol.add_value(field_name='location', value=bldg + '-' + classroom)
                cl.add_value(field_name='occurrences', value=ol.load_item())

            yield(cl.load_item())

        if reached_lower_bound_year or reached_empty_page:
            # finish scraping one target url. Remove it from list
            msg = self.reach_lower_bound_year_msg.format(str(self.year_lower_bound)) \
                if reached_lower_bound_year else self.reach_empty_page_msg
            logging.log(logging.INFO, msg)
            logging.log(logging.INFO, "Finish scraping url {}".format(self.current_url))
            # remove the school that we've scraped from the list
            self.schools.pop(0)
            if self.schools:
                # continue scraping if list of target schools is not empty
                self.update_school_in_url(self.schools)
                logging.log(logging.INFO, "Start scraping url {}".format(self.current_url))
                yield Request(self.current_url, callback=self.parse, dont_filter=True)
            else:
                raise CloseSpider(self.close_spider_msg)
        else:
            self.increment_page_in_url_by(1)
            yield Request(self.current_url, callback=self.parse, dont_filter=True)

    def correct_nbsp(self, string):
        return self.undecided_string if string == u'\xa0' else string

    def correct_nbsp_in_list(self, ls):
        return [self.correct_nbsp(s) for s in ls]

    def period_to_minutes(self, period):
        p_t_m = {
            '1s': 540,
            '1e': 630,
            '2s': 640,
            '2e': 730,
            '3s': 780,
            '3e': 870,
            '4s': 885,
            '4e': 975,
            '5s': 990,
            '5e': 1080,
            '6s': 1095,
            '6e': 1185,
            '7s': 1195,
            '7e': 1285
        }
        try:
            return p_t_m[period]
        except KeyError:
            return -1

    def increment_page_in_url_by(self, increment):
        self.current_page += increment
        self.current_url = customize_url(self.basic_url, self.display_lang, self.term, self.current_school,
                                         self.teaching_lang, self.search_keyword, self.results_per_page,
                                         self.current_page, self.academics_json)

    def update_school_in_url(self, schools):
        self.current_school = schools[0]
        self.current_page = self.start_page
        self.current_url = customize_url(self.basic_url, self.display_lang, self.term, self.current_school,
                                         self.teaching_lang, self.search_keyword, self.results_per_page,
                                         self.current_page, self.academics_json)
