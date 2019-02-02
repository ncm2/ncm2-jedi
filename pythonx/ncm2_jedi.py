# -*- coding: utf-8 -*-

from __future__ import absolute_import
import vim
from ncm2 import Ncm2Source, getLogger
import re
import jedi
import os
from jedi import settings

logger = getLogger(__name__)

import_pat = re.compile(r'^\s*(from|import)')
callsig_pat = re.compile(r'^\s*(?!from|import).*?[(,]\s*$')


class Source(Ncm2Source):

    def __init__(self, vim):
        Ncm2Source.__init__(self, vim)

        env = vim.vars['ncm2_jedi#environment']
        if not env:
            self._env = jedi.get_default_environment()
        else:
            self._env = jedi.create_environment(env)

        rc_settings = vim.vars['ncm2_jedi#settings']
        for name in rc_settings:
            setattr(settings, name, rc_settings[name])

    def get_env(self):
        return self._env

    def on_complete(self, ctx, lines):
        path = ctx['filepath']
        typed = ctx['typed']
        lnum = ctx['lnum']
        startccol = ctx['startccol']
        ccol = ctx['ccol']

        # jedi doesn't work on comment
        # https://github.com/roxma/nvim-completion-manager/issues/62
        if typed.find('#') != -1:
            return

        # replace f" or f' for " or ' respectively to avoid jedi fstrings bug
        typed = re.sub(r"""f("|')""", "\1", typed)
        src = "\n".join([re.sub(r"""f("|')""", "\1", line) for line in lines])
        src = self.get_src(src, ctx)
        if not src.strip():
            # empty src may possibly block jedi execution, don't know why
            logger.info('ignore empty src [%s]', src)
            return

        logger.info('context [%s]', ctx)

        env = self.get_env()
        script = jedi.Script(src, lnum, len(typed), path, environment=env)

        is_import = False
        if import_pat.search(typed):
            is_import = True

        if callsig_pat.search(typed):

            sig_text = ''
            sig = None
            try:
                signatures = script.call_signatures()
                logger.info('signatures: %s', signatures)
                if len(signatures) > 0:
                    sig = signatures[-1]
                    params = [param.description for param in sig.params]
                    sig_text = sig.name + '(' + ', '.join(params) + ')'
                    logger.info("signature: %s, name: %s",
                                sig, sig.name)
            except Exception as ex:
                logger.exception("signature text failed %s", sig_text)

            if sig_text:
                matches = [
                    dict(word='', empty=1, abbr=sig_text, dup=1), ]
                # refresh=True
                # call signature popup doesn't need to be cached by the
                # framework
                self.complete(ctx, ccol, matches, 1)
            return

        completions = script.completions()
        logger.info('completions %s', completions)

        matches = []

        for complete in completions:

            insert = complete.complete

            item = dict(word=ctx['base'] + insert,
                        icase=1,
                        dup=1,
                        menu=complete.description,
                        info=complete.docstring())

            # Fix the user typed case
            if item['word'].lower() == complete.name.lower():
                item['word'] = complete.name

            item = self.match_formalize(ctx, item)

            # snippet support
            try:
                if (complete.type == 'function' or complete.type == 'class'):
                    self.render_snippet(item, complete, is_import)
            except Exception as ex:
                logger.exception(
                    "exception parsing snippet for item: %s, complete: %s", item, complete)

            matches.append(item)

        logger.info('matches %s', matches)
        # workaround upstream issue by letting refresh=True. #116
        self.complete(ctx, startccol, matches)


    def render_snippet(self, item, complete, is_import):

        doc = complete.docstring()

        # This line has performance issue
        # https://github.com/roxma/nvim-completion-manager/issues/126
        # params = complete.params

        fundef = doc.split("\n")[0]

        params = re.search(r'(?:_method|' + re.escape(complete.name) + ')' + r'\((.*)\)', fundef)

        if params:
            item['menu'] = fundef

        logger.debug("building snippet [%s] type[%s] doc [%s]", item['word'], complete.type, doc)

        if params and not is_import:

            num = 1
            placeholders = []
            snip_args = ''

            params = params.group(1)
            if params != '':
                params = params.split(',')
                cnt = 0
                for param in params:
                    cnt += 1
                    if "=" in param or "*" in param or param[0] == '[':
                        break
                    else:
                        name = param.strip('[').strip(' ')

                        # Note: this is not accurate
                        if cnt==1 and (name=='self' or name=='cls'):
                            continue

                        ph = self.snippet_placeholder(num, name)
                        placeholders.append(ph)
                        num += 1

                        # skip optional parameters
                        if "[" in param:
                            break

                snip_args = ', '.join(placeholders)
                if len(placeholders) == 0:
                    # don't jump out of parentheses if function has
                    # parameters
                    snip_args = self.snippet_placeholder(1)

            ph0 = self.snippet_placeholder(0)
            snippet = '%s(%s)%s' % (item['word'], snip_args, ph0)

            item['user_data']['is_snippet'] = 1
            item['user_data']['snippet'] = snippet
            logger.debug('snippet: [%s] placeholders: %s', snippet, placeholders)

    def snippet_placeholder(self, num, txt=''):
        txt = txt.replace('\\', '\\\\')
        txt = txt.replace('$', r'\$')
        txt = txt.replace('}', r'\}')
        if txt == '':
            return '${%s}' % num
        return '${%s:%s}'  % (num, txt)

try:
    # set RLIMIT_DATA
    # https://github.com/roxma/nvim-completion-manager/issues/62
    import resource
    import psutil
    mem = psutil.virtual_memory()
    resource.setrlimit(resource.RLIMIT_DATA,
                       (mem.total/3, resource.RLIM_INFINITY))
except Exception as ex:
    logger.exception('set RLIMIT_DATA failed')

source = Source(vim)

on_complete = source.on_complete
