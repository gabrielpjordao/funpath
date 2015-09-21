# Funpath
### An extensible framework for identifying HTML elements with Machine Learning, using visual features.

Warning: This is a very early stage prototype. No tests or documentation. 
Use it at your own risk :-)

## How it works

### Creating a custom Element Classifier:
```python
class TitleElementClassifier(BaseHTMLElementClassifier):
    feature_extractor_names = (
        'number_of_words',
        'tag',
        'parent_tag',
        'font_size',
        'similarity_with_meta_title',
        'number_of_children',
        'font_weight')

    element_name = 'title'
```

The above example will create a title classifier using the features from `feature_extractor_names`. All of these are already implemented on `funpath.ml.feature_extraction.core_extractors`, but you can create a new one by using:

```python
from funpath.ml.feature_extraction import feature_extractor

@feature_extractor
def element_tag(element, **ctx):
    return element['tag']
```

You can extract features from other resources as well. They are available through keyword arguments ( `**ctx`, for example).

After creating a class that extends `BaseHTMLElementClassifier`, you can then train a classifier for your own dataset. For instance:
```python
my_dataset = [...] # List of funpath.html_extraction.PageResource
classifier = TitleElementClassifier()
classifier.build_from_page_resources(my_dataset)
```

and then extract elements from pages

```python
classifier.classify(url=some_url)
```
