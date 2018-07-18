if get(s:, 'loaded', 0)
    finish
endif
let s:loaded = 1

let g:ncm2_jedi#python_version = get(g:,
            \ 'ncm2_jedi#python_version',
            \ 3)

if g:ncm2_jedi#python_version != 2
    let g:ncm2_jedi#proc = yarp#py3('ncm2_jedi')
else
    " FIXME python2 has wired error message, but it is still usable, I
    " don't know what's wrong
    let g:ncm2_jedi#proc = yarp#py('ncm2_jedi')
endif

let g:ncm2_jedi#source = extend(get(g:, 'ncm2_jedi#source', {}), {
            \ 'name': 'jedi',
            \ 'ready': 0,
            \ 'priority': 9,
            \ 'mark': 'py',
            \ 'scope': ['python'],
            \ 'subscope_enable': 1,
            \ 'complete_pattern': [
            \       '^\s*(import|from).*\s',
            \       '\.',
            \       '\(\s?',
            \       ',\s?'],
            \ 'on_complete': 'ncm2_jedi#on_complete',
            \ 'on_warmup': 'ncm2_jedi#on_warmup',
            \ }, 'keep')

let g:ncm2_jedi#proc.on_load = {-> ncm2#set_ready(g:ncm2_jedi#source)}

func! ncm2_jedi#init()
    call ncm2#register_source(g:ncm2_jedi#source)
endfunc

func! ncm2_jedi#on_warmup(ctx)
    call g:ncm2_jedi#proc.jobstart()
endfunc

func! ncm2_jedi#on_complete(ctx)
    call g:ncm2_jedi#proc.try_notify('on_complete', a:ctx, getline(1, '$'))
endfunc

