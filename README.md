# ncm2-jedi

Python completion for ncm2 via the greate
[jedi](https://github.com/davidhalter/jedi) library.

## Config

### `g:ncm2_jedi#python_version`

Defaults to 3.

If set to `2`, the jedi completion process is started with the python
specified by `:help g:python_host_prog`.

If set to `3`, the jedi completion process is started with the python
specified by `:help g:python3_host_prog`.

### `g:ncm2_jedi#environment`

When you have virtualenv, you could set this variable to the python executable
of your virtualenv.

Read
[jedi-environments](https://jedi.readthedocs.io/en/latest/docs/api.html#environments)
for more information.
