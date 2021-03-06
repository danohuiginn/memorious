import os
import logging
from fnmatch import fnmatch

from memorious.logic.crawler import Crawler

log = logging.getLogger(__name__)


class CrawlerManager(object):
    """Crawl a directory of YAML files to load a set of crawler specs."""

    def __init__(self):
        self.crawlers = {}

    def load_path(self, path):
        if not os.path.isdir(path):
            log.warning('Crawler config path %s not found.', path)

        for root, _, file_names in os.walk(path):
            for file_name in file_names:
                if not (fnmatch(file_name, '*.yaml') or fnmatch(file_name, '*.yml')):
                    continue
                source_file = os.path.join(root, file_name)
                crawler = Crawler(self, source_file)
                self.crawlers[crawler.name] = crawler

    def run_scheduled(self):
        log.info('%s crawlers found' % len(self.crawlers))
        for crawler in self:
            if crawler.delta is None:
                log.info('[%s] has no schedule.', crawler.name)
                return
            if crawler.check_due():
                log.info('[%s] due.', crawler.name)
                crawler.run()
            else:
                log.info('[%s] not due.', crawler.name)

    def run_cleanup(self):
        log.info('%s crawlers found' % len(self.crawlers))
        for crawler in self:
            crawler.cleanup()

    def __getitem__(self, name):
        return self.crawlers.get(name)

    def __iter__(self):
        crawlers = list(self.crawlers.values())
        crawlers.sort(key=lambda c: c.name)
        return iter(crawlers)

    def __len__(self):
        return len(self.crawlers)

    def get(self, name):
        return self.crawlers.get(name)
