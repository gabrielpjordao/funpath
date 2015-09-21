from copy import deepcopy
from itertools import imap, chain
from StringIO import StringIO

import requests
import premailer
from cached_property import cached_property
from lxml.html import tostring, etree
from lxml.cssselect import CSSSelector

from funpath.utils import AttrDict, strip_tags, parse_css_style


class DOMTree(object):
    """
      This class is an abstraction over an lxml tree. It provides some utilities
      for interacting with the DOM. On top of that, it deals with cleaning up and
      mapping its elements.
    """

    def __init__(self, page_source, elements=None):
        parser = etree.HTMLParser()
        self.tree = etree.parse(StringIO(page_source), parser)
        self.elements = elements or tuple(imap(self._map_lxml_element, self.tree.iter(tag=etree.Element)))
        self.root_xpath = self._get_xpath(self.tree.getroot())

    def _get_xpath(self, lxml_element):
        return self.tree.getpath(lxml_element)

    def stringify_children(self, node):
        parts = ([node.text] +
                 list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
                 [node.tail])
        # Removes possible Nones in texts and tails
        return strip_tags(''.join(filter(None, parts)))

    def _parse_style_attributes(self, lxml_element):
        return parse_css_style(lxml_element.attrib.get('style', ''))

    def is_xpath_root(self, xpath):
        return self.root_xpath == xpath

    def _map_lxml_element(self, lxml_element, parse_styles=True):
        parent_element = lxml_element.getparent()
        xpath = self._get_xpath(lxml_element)
        return AttrDict(
            xpath=xpath,
            tag=lxml_element.tag,
            style_attributes=self._parse_style_attributes(lxml_element) if parse_styles else None,
            attributes={k: v for k, v in lxml_element.attrib.items()},
            text=self.stringify_children(lxml_element),
            parent_xpath=self._get_xpath(parent_element) if parent_element is not None else None,
            child_xpaths=map(self._get_xpath, lxml_element.findall('.//')))

    def find_element(self, selector_type, selector):
        elements = None
        if selector_type == 'css':
            elements = self.find_element_by_cssselector(selector)
        else:
            elements = self.find_element_by_xpath(selector)
        return elements[0] if elements else None

    def find_element_by_cssselector(self, selector):
        return self._map_lxml_element(CSSSelector(selector)(self.tree.getroot()))

    def find_element_by_xpath(self, selector, parse_styles=True):
        elements = self.tree.getroot().xpath(selector)
        return self._map_lxml_element(elements[0], parse_styles) if elements else None


def add_visual_attributes(browser, element):
    try:
        visual_element = browser.find_element_by_xpath(element.xpath)
    except NoSuchElementException as e:
        return

    is_visible = visual_element.is_displayed()
    if not is_visible:
        return None

    element_location = visual_element.location
    element_size = visual_element.size

    visual_attributes = {
      'is_visible': is_visible,
      'x_location': element_location['x'],
      'y_location': element_location['y'],
      'width': element_size['width'],
      'height': element_size['height'],
      'font_weight': visual_element.value_of_css_property('font-weight'),
      'font_size': visual_element.value_of_css_property('font-size')
    }
    return element.xpath, AttrDict(**dict(deepcopy(element).items() + visual_attributes.items()))


class PageResource(object):

    def __init__(self, json_resource=None, json_resource_path=None, url=None,
                 classified_elements=None, cached_elements=None):

        self.classified_elements = classified_elements or ()
        self.url = url or json_resource['url']

        if json_resource or json_resource_path:
            self.load_json(json_resource, json_resource_path)
        if url:
            self.download()

        self.dom_tree = DOMTree(self.inlined_source, elements=cached_elements)

    def load_json(self, json_resource, json_resource_path):
        if json_resource_path:
            with open(json_resource_path) as _f:
                json_resource = json.loads(_f.read())

        self.__dict__.update(json_resource)

    def download(self):
        self.source = requests.get(self.url).content.decode('utf-8')
        self.inlined_source = premailer.Premailer(self.source, base_url=self.url).transform().encode('utf-8')

    @cached_property
    def element_map(self):
        return {el['xpath']: el for el in self.dom_tree.elements}

    @cached_property
    def computed_styles(self):
        """
          Gets a map with the keys being the xpaths from the element's tree
          and the values being a dict with the computed style attributes.

          Note that this list of computed styles is not perfect and does
          not guarantee that an element really has this style.

          It guarantees, however, that each CSS attribute has the higher precedence
          for each element. To illustrate, take the following HTML snippet:

          <div style="font-size: 10px">
             <h1 style="font-size: 15px;"><a>title</a></h1>
             <h2>title2</h1>
          </div>

          In the above code, `h1  a` will have font-size 15px and `h2` font-size 10px.
          since `h1` has higher precedence over `div`, in this specific scenario.
        """
        elements_with_css_computed = {}
        computed_styles = {}

        # We only compute body elements having text to avoid useless processing
        for element in filter(lambda e: '/body' in e['xpath'] and not e['text'].isspace(),
                              self.dom_tree.elements):
            styles_until_parent = []
            parent_xpath = element['xpath']
            while not self.dom_tree.is_xpath_root(parent_xpath):
                styles_until_parent.append(self.element_map[parent_xpath]['style_attributes'])
                parent_xpath = self.element_map[parent_xpath]['parent_xpath']

            element_computed_styles = {k: v for style in reversed(styles_until_parent)
                                       for k, v in style.items()}
            computed_styles[element['xpath']] = element_computed_styles
        return computed_styles

    @property
    def json_repr(self):
        return {
            'classified_elements': self.classified_elements,
            'inlined_source': self.inlined_source,
            'original_source': self.original_source,
            'url': self.url
        }

