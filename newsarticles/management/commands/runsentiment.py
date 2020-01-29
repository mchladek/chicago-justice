import logging
from django.core.management.base import BaseCommand, CommandError

from newsarticles.scrapers import sentiment

LOG = logging.getLogger(__name__)

RUN_SCRIPT_BOTH = 'both'

class Command(BaseCommand):
    help = "Run binning and/or sentiment analysis on articles"

    def add_arguments(self, parser):
        parser.add_argument('run_script', nargs='?', default=RUN_SCRIPT_BOTH, help='Which sentiment script to run: bin articles (bin), analyze articles (analyze), or both bin and analyze (both)')

    def handle(self, *args, **options):
        if options['run_script'] == 'bin':
            LOG.info('Running binning script on articles')
            sentiment.bin_all_articles()
        elif options['run_script'] == 'analyze':
            LOG.info('Running sentiment analysis on articles')
            sentiment.analyze_all_articles()
        elif options['run_script'] == RUN_SCRIPT_BOTH:
            LOG.info('Running both binning script and sentiment analysis on articles')
            sentiment.bin_all_articles()
            sentiment.analyze_all_articles()
        else:
            raise CommandError('Command argument could not be parsed')