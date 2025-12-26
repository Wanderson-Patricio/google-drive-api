import logging


class Logger:
    def __init__(self, 
                 app_name: str, 
                 level = logging.INFO) -> None:
        
        logging.basicConfig(
            format='%(levelname)s - %(asctime)s - %(name)s  - %(message)s',
            filename='log.log',
            filemode='a',
            encoding='utf-8'
            )
        
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(level)

    def log(self, message, level=logging.INFO):
        if level >= self.logger.level:
            self.logger.log(level, message)

    def debug(self, message):
        self.log(message, logging.DEBUG)

    def info(self, message):
        self.log(message, logging.INFO)

    def warning(self, message):
        self.log(message, logging.WARNING)

    def error(self, message):
        self.log(message, logging.ERROR)

    def critical(self, message):
        self.log(message, logging.CRITICAL)