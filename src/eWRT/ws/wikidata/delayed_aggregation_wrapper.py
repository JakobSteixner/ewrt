#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on October 09, 2018

@author: jakob <jakob.steixner@modul.ac.at>

Collects selected meta-info about entities from Wikidata, allowing to
postpone the supplementation with Wikipedia content for better performance
by caching the Wikidata-only entities and storing a mapping between them and
the Wikipedia page identifiers from which to supplement them.


'''

import logging

from collections import OrderedDict

from eWRT.ws.wikidata.bundle_wikipedia_requests import \
    collect_multiple_from_wikipedia
from eWRT.ws.wikidata.extract_meta import WikidataEntityIterator

logger = logging.Logger(name='wp_bundler')


def collect_entities_delayed(entity_types,
                             retrieval_mode,
                             include_wikipedia=False,
                             wikidata_postprocessing_steps=None,
                             languages=None,
                             n_queries=1,
                             delay_wikipedia_retrieval=False,
                             limit_per_query=1000,
                             dump_path=None,
                             memory_saving_limit=50,
                             **kwargs):
    """

    :param wikidata_postprocessing_steps:
    :param dump_path:
    :param entity_types: dict/Ordered dict of entity types
    :param retrieval_mode: read entities from API or dumped file.
    :param n_queries: number of subsequent queries, with automatic offset
        (only used with retrieval mode API)
    :param languages: list of languages (ISO code)
    :param limit_per_query: limit
    :param delay_wikipedia_retrieval:
    :param include_wikipedia:
    :param memory_saving_limit:
    :return:
    """
    if wikidata_postprocessing_steps is None:
        wikidata_postprocessing_steps = []
    if languages is None:
        languages = ['en']
    relevant_entity_types = OrderedDict(
        [(entity_type, entity_types[entity_type]) for entity_type in
         entity_types])
    iterator = WikidataEntityIterator(relevant_entity_types,
                                      dump_path=dump_path)
    if retrieval_mode == 'API':
        collect_entities_iterative = iterator.collect_entities_iterative
    elif retrieval_mode == 'dump':
        collect_entities_iterative = iterator.collect_entities_from_dump
        n_queries = 1  # starting a query with an offset is undefined for
        # dump mode, multiple queries would thus just produce the same
        # result over again.
    else:
        raise NotImplementedError('Supported modes are: API and dump!')
    for n in range(n_queries +1):
        wikipedia_sitelinks_to_retrieve = {lang: {} for lang in languages}
        entities_retrieved = {}
        for idx, entity_data in enumerate(
                collect_entities_iterative(limit_per_query=limit_per_query,
                                           languages=languages,
                                           n_queries=n_queries,
                                           include_wikipedia=include_wikipedia,
                                           delay_wikipedia_retrieval=delay_wikipedia_retrieval,
                                           **kwargs)):
            for step, param_dict in wikidata_postprocessing_steps:
                entity_data = step(entity=entity_data, **param_dict)
            if include_wikipedia:
                entities_retrieved[entity_data['url']] = entity_data
                if delay_wikipedia_retrieval:
                    for lang in languages:
                        try:

                            wikipedia_sitelinks_to_retrieve[lang][
                                entity_data[lang + 'wiki']] = entity_data['url']

                        except (KeyError,):
                            pass

                if not delay_wikipedia_retrieval:
                    for merged_result in collect_multiple_from_wikipedia(
                            wikipedia_sitelinks_to_retrieve,
                            entities_retrieved):
                        yield merged_result
                    wikipedia_sitelinks_to_retrieve = {lang: {} for lang in
                                                       languages}
                    entities_retrieved = {}
                    if idx >= limit_per_query:
                        break

            if idx >= limit_per_query or (delay_wikipedia_retrieval and
                                          include_wikipedia and
                                          (idx + 1) % memory_saving_limit == 0):
                # if debug:
                #     logger.debug(datetime.datetime.now().isoformat())
                #     logger.debug('retrieving data from wikipedia')
                #     for language in wikipedia_sitelinks_to_retrieve:
                #         print('{} entries bookmarked in language {}'.format(
                #             len(wikipedia_sitelinks_to_retrieve[language]),
                #             language
                #         ))
                for raw in entities_retrieved.values():
                    if not any((e.endswith('wiki') for e in raw)):
                        raise ValueError(
                            'Entity {} without any wikipedia '
                            'sitelinks'.format(raw['wikidata_id'])
                        )
                for merged_result in collect_multiple_from_wikipedia(
                        wikipedia_sitelinks_to_retrieve,
                        entities_retrieved):
                    yield merged_result
                    continue
                # reset caches:
                wikipedia_sitelinks_to_retrieve = {lang: {} for lang in
                                                   languages}
                entities_retrieved = {}
                if idx >= limit_per_query:
                    break
            elif not delay_wikipedia_retrieval:
                from eWRT.ws.wikidata.bundle_wikipedia_requests import \
                    batch_enrich_from_wikipedia
                for language in languages:
                    try:
                        for entry in batch_enrich_from_wikipedia(
                                wikipedia_pages={
                                    language: {
                                        entity_data[language + 'wiki']['title']:
                                            entity_data['url']
                                    }
                                },
                                entities_cache={
                                    entity_data['url']: entity_data
                                },
                                language=language):
                            yield entry

                    except KeyError as e:
                        pass

                    yield entity_data
        print('Successfully parsed {} entities!'.format(idx))

        for merged_result in collect_multiple_from_wikipedia(
                wikipedia_sitelinks_to_retrieve,
                entities_retrieved):
            yield merged_result
