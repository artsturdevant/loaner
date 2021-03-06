# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for backend.lib.search."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import parameterized
import mock

from google.appengine.api import search

import endpoints

from loaner.web_app.backend.api.messages import shared_messages
from loaner.web_app.backend.api.messages import shelf_messages
from loaner.web_app.backend.lib import search_utils
from loaner.web_app.backend.models import shelf_model
from loaner.web_app.backend.testing import loanertest


class SearchTest(loanertest.EndpointsTestCase, parameterized.TestCase):

  @parameterized.parameters(
      (shelf_messages.Shelf(location='NY', capacity=50),
       'location:NY capacity:50 enabled:True',),
      (shelf_messages.Shelf(location='NY', capacity=50, enabled=False),
       'location:NY capacity:50 enabled:False',))
  def test_to_query(self, message, expected_query):
    """Tests the creation of a valid search query from ndb properties."""
    query = search_utils.to_query(message, shelf_model.Shelf)
    #  The query is split because ndb properties are unordered when called by
    #  model_class._properties. This test would be flaky otherwise.
    self.assertCountEqual(query.split(' '), expected_query.split(' '))

  @mock.patch.object(search_utils, 'logging', autospec=True)
  def test_document_to_message(self, mock_logging):
    """Tests the creation of a protorpc message from a search document."""
    test_search_document = search.ScoredDocument(
        doc_id='test_doc_id',
        fields=[
            search.NumberField(name='capacity', value=20.0),
            search.TextField(name='location', value='US MTV'),
            search.AtomField(name='location', value='US-MTV'),
            search.AtomField(name='enabled', value='True'),
            search.GeoField(
                name='lat_long', value=search.GeoPoint(52.37, 4.88)),
            search.TextField(name='not_present', value='MTV')])
    expected_message = shelf_messages.Shelf(
        enabled=True, location='US-MTV', capacity=20, latitude=52.37,
        longitude=4.88)

    response_message = search_utils.document_to_message(
        test_search_document, shelf_messages.Shelf())
    self.assertEqual(response_message, expected_message)
    self.assertTrue(response_message.enabled)
    assert mock_logging.error.call_count == 1

  def test_get_search_cursor(self):
    """Tests the creation of a search cursor with a web_safe_string."""
    expected_cursor_web_safe_string = 'False:ODUxODBhNTgyYTQ2ZmI0MDU'
    returned_cursor = (
        search_utils.get_search_cursor(
            expected_cursor_web_safe_string))
    self.assertEqual(
        expected_cursor_web_safe_string, returned_cursor.web_safe_string)

  @mock.patch.object(search, 'Cursor', autospec=True)
  def test_get_search_cursor_error(self, mock_cursor):
    """Tests the creation of a search cursor when an error occurs."""
    mock_cursor.side_effect = ValueError
    with self.assertRaisesWithLiteralMatch(
        endpoints.BadRequestException,
        search_utils._CORRUPT_KEY_MSG):
      search_utils.get_search_cursor(None)

  @parameterized.named_parameters(
      {'testcase_name': 'QueryStringOnly',
       'request': shared_messages.SearchRequest(query_string='enrolled:True'),
       'expected_values': ('enrolled:True', None, [])
      },
      {'testcase_name': 'QueryStringWithReturnedFields',
       'request': shared_messages.SearchRequest(
           query_string='location:US-NYC', returned_fields=['location']),
       'expected_values': ('location:US-NYC', None, ['location'])
      },
  )
  def test_set_search_query_options(self, request, expected_values):
    """Tests setting the query options without sort options from message."""
    returned_query, returned_sort_options, returned_returned_fields = (
        search_utils.set_search_query_options(request))
    expected_query, expected_sort_options, expcted_returned_fields = (
        expected_values)
    self.assertEqual(expected_sort_options, returned_sort_options)
    self.assertEqual(expected_query, returned_query)
    self.assertEqual(expcted_returned_fields, returned_returned_fields)

  @parameterized.named_parameters(
      {'testcase_name': 'ExpressionWithDirection',
       'request': shared_messages.SearchRequest(
           query_string='enrolled:True',
           expressions=[shared_messages.SearchExpression(
               expression='enrolled',
               direction=shared_messages.SortDirection.ASCENDING)]),
       'expected_sort_options_expressions': [search.SortExpression(
           expression='enrolled', direction=search.SortExpression.ASCENDING)]
      },
      {'testcase_name': 'MultipleExpressionsWithDirection',
       'request': shared_messages.SearchRequest(
           query_string='enrolled:True',
           expressions=[
               shared_messages.SearchExpression(
                   expression='enrolled',
                   direction=shared_messages.SortDirection.ASCENDING),
               shared_messages.SearchExpression(
                   expression='serial_number',
                   direction=shared_messages.SortDirection.DESCENDING)
           ]),
       'expected_sort_options_expressions': [
           search.SortExpression(
               expression='enrolled',
               direction=search.SortExpression.ASCENDING),
           search.SortExpression(
               expression='serial_number',
               direction=search.SortExpression.DESCENDING)
       ]
      },
      {'testcase_name': 'ExpressionWithoutDirection',
       'request': shared_messages.SearchRequest(
           query_string='enrolled:True',
           expressions=[shared_messages.SearchExpression(
               expression='enrolled')]),
       'expected_sort_options_expressions': [search.SortExpression(
           expression='enrolled')]
      },
      {'testcase_name': 'MultipleExpressionsWithoutDirection',
       'request': shared_messages.SearchRequest(
           query_string='enrolled:True',
           expressions=[
               shared_messages.SearchExpression(
                   expression='enrolled'),
               shared_messages.SearchExpression(
                   expression='serial_number')
           ]),
       'expected_sort_options_expressions': [
           search.SortExpression(
               expression='enrolled',
               direction=search.SortExpression.DESCENDING),
           search.SortExpression(
               expression='serial_number',
               direction=search.SortExpression.DESCENDING)
       ]
      },
  )
  def test_set_search_query_options_with_sort_options(
      self, request, expected_sort_options_expressions):
    """Tests setting query options with sort options from message."""
    returned_query, returned_sort_options, returned_returned_fields = (
        search_utils.set_search_query_options(request))
    del returned_query  # Unused.
    del returned_returned_fields  # Unused.
    for i in range(len(returned_sort_options.expressions)):
      self.assertEqual(
          returned_sort_options.expressions[i].expression,
          expected_sort_options_expressions[i].expression)
      self.assertEqual(
          returned_sort_options.expressions[i].direction,
          expected_sort_options_expressions[i].direction)


if __name__ == '__main__':
  loanertest.main()
