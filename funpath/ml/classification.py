from functools import partial

from cached_property import cached_property
from sklearn.feature_extraction import DictVectorizer
from sklearn import svm
from sklearn.preprocessing import LabelEncoder

from funpath.utils import NotImplementedField, unzip, flatten
from funpath.html_extraction import PageResource
from funpath.ml.feature_extraction import NOT_CLASSIFIED_ELEMENT_NAME, apply_extractors


class BaseHTMLElementClassifier(object):

    feature_extractor_names = NotImplementedField
    element_name = NotImplementedField

    @cached_property
    def label_encoder(self):
        encoder = LabelEncoder()
        encoder.fit([self.element_name, NOT_CLASSIFIED_ELEMENT_NAME])
        return encoder

    def print_reports(self):
        print(classification_report(clf.predict(a_test), b_test, target_names=label_encoder.classes_.tolist()))

    @cached_property
    def vectorizer(self):
        return DictVectorizer()

    def extract_features(self, page, element):
        return apply_extractors(
            self.feature_extractor_names,
            page=page,
            element=element
        )

    def _remap_classifications(self, page):
        """
        Since pages may have training for different elements,
        we take off them.
        """
        page.classified_elements = {
          k: v for k, v in page.classified_elements.items()
          if v == self.element_name
        }


    def build_from_page_resources(self, page_resources):
        for page in page_resources:
            self._remap_classifications(page)

        # Generates a list of tuples containing page element features
        # along with their classifications
        features, classifications = unzip(flatten(
            map(lambda page:
                    map(lambda e: (
                            self.extract_features(page, e),
                            page.classified_elements.get(e['xpath'], NOT_CLASSIFIED_ELEMENT_NAME)),
                        filter(lambda e: '/body'in e['xpath'] and not e['text'].isspace(),
                                page.dom_tree.elements)
                       ),
                page_resources)
        ))
        return self.build(features, classifications)

    def build(self, features, classifications):
        transformed_features = self.vectorizer.fit_transform(features).tocsr()
        transformed_labels = self.label_encoder.transform(classifications)

        # TODO: Make it generic and allow Pipelines
        self.classifier = svm.LinearSVC()
        self.classifier.fit(transformed_features, transformed_labels)
        return self.classifier

    def classify(self, url=None, page=None):
        page = page or PageResource(url=url)
        features = [self.extract_features(page, e) for e in page.dom_tree.elements]
        transformed_features = self.vectorizer.transform(features)
        transformed_classifications = self.classifier.predict(transformed_features)
        classifications = self.label_encoder.inverse_transform(transformed_classifications)

        # Returns a list with tuples containig elements and their features.
        # It will only return elements that match the expected element name.
        return map(lambda (e, f, c): (e, f),
                   filter(lambda (e, f, c): c == self.element_name,
                          zip(page.dom_tree.elements, features, classifications)))


