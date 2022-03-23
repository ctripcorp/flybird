# -*- coding: utf-8 -*-
# @Time : 2022/3/22 17:12
# @Author : hyx
# @File : active_tag.py
# @desc : active_tag 

from behave.tag_matcher import ActiveTagMatcher, setup_active_tag_values

import flybirds.core.global_resource as gr
from flybirds.core.global_context import GlobalContext
from flybirds.utils import flybirds_log as log


def active_tag_init():
    """
      # -- MATCHES ANY TAGS: @use.with_{category}={value}
     # NOTE:
         active_tag_value_provider provides category values for active tags.
     """
    tag_provider_module = gr.get_value("projectScript").tag_provider
    tag_value_provider = getattr(tag_provider_module,
                                 "ACTIVE_TAG_VALUE_PROVIDER")
    log.info(f'tag_value_provider :{tag_value_provider}')
    active_tag_value_provider = tag_value_provider.copy() \
        if tag_value_provider is not None else {}

    active_tag_matcher = ActiveTagMatcher(active_tag_value_provider)
    gr.set_value("active_tag_matcher", active_tag_matcher)
    return active_tag_value_provider


class OnBeforeAll:
    """
    prepare
    """
    name = "OnBeforeAll"
    order = 0

    @staticmethod
    def can(context):
        return True

    @staticmethod
    def run(context):
        """
          SETUP ACTIVE-TAG MATCHER (with userdata)
          USE: behave -D browser=safari ...
        """
        log.info(f'[before_all] user_data:{context.config.userdata}')
        active_tag_value_provider = active_tag_init()
        log.info(
            f'[before_all] active_tag_value_provider:{active_tag_value_provider}')
        setup_active_tag_values(active_tag_value_provider,
                                context.config.userdata)


class OnBeforeFeature:
    """
    prepare OnBeforeFeature
    """
    name = "OnBeforeFeature"
    order = 5

    @staticmethod
    def can(context, feature):
        return True

    @staticmethod
    def run(context, feature):
        log.info(f'[before_feature] feature.tags:{feature.tags}')
        active_tag_matcher = gr.get_value("active_tag_matcher")
        if active_tag_matcher.should_exclude_with(feature.tags):
            feature.skip(reason=active_tag_matcher.exclude_reason)


class OnBeforeScenario:
    """
    before run scenario will trigger this
    """
    name = "OnBeforeScenario"
    order = 5

    @staticmethod
    def can(context, scenario):
        return True

    @staticmethod
    def run(context, scenario):
        log.info(
            f'[before_scenario] scenario.effective_tags:{scenario.effective_tags}')
        active_tag_matcher = gr.get_value("active_tag_matcher")
        # -- NOTE: scenario.effective_tags := scenario.tags + feature.tags
        if active_tag_matcher.should_exclude_with(scenario.effective_tags):
            scenario.skip(reason=active_tag_matcher.exclude_reason)


var_all = GlobalContext.join("before_run_processor", OnBeforeAll, 1)
var_2 = GlobalContext.join("before_feature_processor", OnBeforeFeature, 1)
var_3 = GlobalContext.join("before_scenario_processor", OnBeforeScenario, 1)
