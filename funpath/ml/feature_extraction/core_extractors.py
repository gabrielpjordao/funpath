import re

from funpath.utils import get_text_similarity
from funpath.ml.feature_extraction import feature_extractor

font_unit_separator_pattern = re.compile(r'^(\d*[.,]{0,1}\d*)(\D+)$')
unit_proportion_multiplier = {'em': 100.0, 'pt': 9.1, 'px': 6.6, '%': 1, 'rem': 100.0}
size_name_map = {
    'xx-small': '5px',
    'x-small': '7px',
    'smaller': '9px',
    'small': '11px',
    'medium': '16px',
    'large': '24px',
    'x-large': '36px',
    'xx-large': '54px'
}
def normalize_font_size(value):
    if value.strip() == '0':
        return 0
    if not value:
        return 1.0
    # TODO: if it's em, rem or %, we have to consider the proportion with parents
    value = size_name_map.get(value, value)
    size, unit = font_unit_separator_pattern.match(value.strip()).groups()
    size_in_percent = float(size) * unit_proportion_multiplier[unit]
    return size_in_percent / 100.0


def normalize_font_weight(value):
    value = value.strip()
    if not value.isdigit():
        # It means it's thick, so it's better to normalize
        if value == 'bolder':
            return 'bold'
        return value
    value = int(value)
    if value <= 300:
        return 'lighter'
    elif value <= 600:
        return 'normal'
    elif value:
        return 'bold'


@feature_extractor
def similarity_with_meta_title(element, page, **ctx):
    meta_title = page.dom_tree.find_element_by_xpath('//title')
    return get_text_similarity(meta_title['text'], element['text'])


@feature_extractor
def tag(element, **ctx):
    return element['tag']


@feature_extractor
def parent_tag(element, page, **ctx):
    return page.element_map.get(element.get('parent_xpath'), {}).get('tag', '')


@feature_extractor
def parent_parent_tag(element, page, **ctx):
    parent = page.element_map.get(element['parent_xpath'], {})
    return parent_tag(parent, page, **ctx)


@feature_extractor
def number_of_children(element, **ctx):
    return len(element['child_xpaths'])


@feature_extractor
def number_of_words(element, **ctx):
    return len(element['text'].replace('\n', '').replace('\t', '').split())


@feature_extractor
def font_size(element, page, **ctx):
    font_size_raw = page.computed_styles.get(element['xpath'], {}).get('font-size', '100%')
    while font_size_raw.strip() == 'inherit':
        element = page.element_map[element['parent_xpath']]
        font_size_raw = page.computed_styles.get(element['xpath'], {}).get('font-size', '100%')
    return normalize_font_size(font_size_raw)


@feature_extractor
def font_weight(element, page, **ctx):
    font_weight_raw = page.computed_styles.get(element['xpath'], {}).get('font-weight', 'normal')
    while font_weight_raw.strip() == 'inherit':
        element = page.element_map[element['parent_xpath']]
        font_weight_raw = page.computed_styles.get(element['xpath'], {}).get('font-weight', 'normal')
    return normalize_font_weight(font_weight_raw)

