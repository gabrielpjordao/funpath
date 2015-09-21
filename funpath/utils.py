import difflib
import re
from HTMLParser import HTMLParser

def parse_unit_number(raw_number):
    """
      Convert string numbers with size units such as 10px, 14pt into numbers.
      It will get all the numbers on the left, before a string.

      For example:
      >>> parse_unit_number('10px')
      10
    """
    return int(''.join(takewhile(lambda x: x.isdigit(), raw_number)))


def unzip(iterable):
     """
     The inverse of Python's `zip` function

     For example:
     >>> unzip([('a', 1), ('b', 2), ('c', 3), ('d', 4)])
     [('a', 'b', 'c', 'd'), (1, 2, 3, 4)]

     """
     return zip(*iterable)


@property
def NotImplementedField(self):
    raise NotImplementedError


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


space_pattern = re.compile(r'\s+')


def remove_spaces(text):
    return re.sub(space_pattern, '', text)


def get_text_similarity(txt1, txt2):
    return difflib.SequenceMatcher(a=remove_spaces(txt1.lower()),
                                   b=remove_spaces(txt2.lower())).ratio()

def parse_css_style(style):
    """
    Simply parse an HTML element style attribute.
    This doesn't have many guarantees, but is simple and fast.
    """
    if not style or ':' not in style:
        return {}
    try:
        return {pair.split(":")[0]: pair.split(":")[1]
                for pair in filter(None, remove_spaces(style).split(";"))}
    except Exception as e:
        return {}

flatten = lambda iterable: [item for sublist in iterable for item in sublist]

