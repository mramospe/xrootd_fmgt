import logging, warnings

l = logging.getLogger('dummy')
c = logging.StreamHandler()
l.setLevel(logging.WARNING)
l.addHandler(c)
formatter = logging.Formatter('%(levelname)s - %(message)s')
c.setFormatter(formatter)
warnings.warn('cacaaaa')
l.info('molo')
l.warn('cacaaa')
