/* Shared UI quality-of-life helpers: searchable selects + live search.
 * Vanilla JS, no dependencies. Loaded via base.html (defer).
 */
(function () {
    'use strict';

    // ── injected styles (self-contained component) ──
    var css = [
        '.searchable-select{position:relative;min-width:0}',
        '.searchable-select .ss-input{cursor:pointer;padding-right:2rem;background-image:url("data:image/svg+xml,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3e%3cpath fill=%27%236c757d%27 d=%27M1.6 5.6 8 12l6.4-6.4-1.2-1.2L8 9.6 2.8 4.4z%27/%3e%3c/svg%3e");background-repeat:no-repeat;background-position:right .6rem center;background-size:1rem}',
        '.searchable-select .ss-input:focus{background-image:none}',
        '.ss-list{position:absolute;top:100%;left:0;right:0;z-index:1050;max-height:240px;overflow:auto;margin:2px 0 0;padding:0;list-style:none;background:#fff;border:1px solid #dee2e6;border-radius:.375rem;box-shadow:0 .5rem 1rem rgba(0,0,0,.15);transform-origin:top center;animation:ssIn 150ms var(--ease-out, cubic-bezier(0.23,1,0.32,1))}',
        '.ss-list li{padding:.4rem .75rem;cursor:pointer;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
        '.ss-list li:hover,.ss-list li.active{background:#0d6efd;color:#fff}',
        '.ss-list li.empty{padding:.5rem .75rem;color:#6c757d;cursor:default;background:#fff}',
        '.ls-clear-btn{border:0;background:transparent;color:#6c757d;padding:0 .45rem;display:none;align-items:center;z-index:5}',
        '.ls-clear-btn:hover{color:#dc3545}',
        '.ls-clear-btn.show{display:inline-flex}',
        '@keyframes ssIn{from{opacity:0;transform:scale(0.98) translateY(-2px)}to{opacity:1;transform:scale(1) translateY(0)}}',
        '@media (prefers-reduced-motion: reduce){.searchable-select .ss-list{animation:none}}'
    ].join('');
    var styleEl = document.createElement('style');
    styleEl.textContent = css;
    document.head.appendChild(styleEl);

    // ── searchable select ──
    function initSearchable(select) {
        if (select.dataset.ssDone) return;
        select.dataset.ssDone = '1';

        var wrapper = document.createElement('div');
        wrapper.className = 'searchable-select';

        var input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control ss-input';
        input.placeholder = select.getAttribute('data-placeholder') || 'Cari atau pilih...';
        input.setAttribute('autocomplete', 'off');
        input.setAttribute('role', 'combobox');
        input.setAttribute('aria-expanded', 'false');
        input.setAttribute('aria-autocomplete', 'list');

        var list = document.createElement('ul');
        list.className = 'ss-list';
        list.setAttribute('role', 'listbox');
        list.hidden = true;

        // cache options once
        var options = Array.prototype.map.call(select.options, function (o) {
            return { value: o.value, text: o.textContent.replace(/\s+/g, ' ').trim() };
        });

        function selectedText() {
            var i = select.selectedIndex;
            return i >= 0 ? options[i].text : '';
        }

        input.value = selectedText();

        function render(filter) {
            list.textContent = '';
            var f = (filter || '').toLowerCase();
            var matches = 0;
            options.forEach(function (o) {
                if (f && o.text.toLowerCase().indexOf(f) === -1) return;
                var li = document.createElement('li');
                li.textContent = o.text;
                li.setAttribute('role', 'option');
                li.dataset.value = o.value;
                if (select.value === o.value) li.classList.add('active');
                list.appendChild(li);
                matches++;
            });
            if (!matches) {
                var empty = document.createElement('li');
                empty.className = 'empty';
                empty.textContent = 'Tidak ada hasil';
                list.appendChild(empty);
            }
            return matches;
        }

        function open() {
            var any = render(input.value);
            list.hidden = false;
            input.setAttribute('aria-expanded', 'true');
            list.setAttribute('aria-activedescendant', '');
            // keep chosen option in view
            var active = list.querySelector('li.active');
            if (active && any) {
                active.scrollIntoView({ block: 'nearest' });
                input.setAttribute('aria-activedescendant', active.textContent);
            }
        }
        function close() {
            list.hidden = true;
            input.setAttribute('aria-expanded', 'false');
        }

        function pick(li) {
            if (!li || !li.dataset.value) return;
            select.value = li.dataset.value;
            input.value = li.textContent;
            // notify native select listeners (e.g. resident-field refill)
            select.dispatchEvent(new Event('change', { bubbles: true }));
            close();
        }

        function activeLi() { return list.querySelector('li.active'); }
        function move(dir) {
            if (list.hidden) { open(); return; }
            var items = list.querySelectorAll('li:not(.empty)');
            if (!items.length) return;
            var cur = activeLi();
            var idx = Array.prototype.indexOf.call(items, cur);
            idx = (idx + dir + items.length) % items.length;
            items.forEach(function (li) { li.classList.remove('active'); });
            items[idx].classList.add('active');
            items[idx].scrollIntoView({ block: 'nearest' });
        }

        input.addEventListener('focus', open);
        input.addEventListener('click', function () { if (list.hidden) open(); });
        input.addEventListener('input', function () { open(); });
        input.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
            else if (e.key === 'Enter') {
                e.preventDefault();
                var a = activeLi();
                if (a && !list.hidden) pick(a);
                else close();
            }
            else if (e.key === 'Escape') { close(); input.blur(); }
            else if (e.key === 'Tab') close();
        });
        list.addEventListener('mousedown', function (e) {
            e.preventDefault(); // keep focus in input
            var li = e.target.closest('li:not(.empty)');
            if (li) pick(li);
        });
        document.addEventListener('click', function (e) {
            if (!wrapper.contains(e.target)) close();
        });

        wrapper.appendChild(input);
        wrapper.appendChild(list);
        select.parentNode.insertBefore(wrapper, select);
        select.classList.add('visually-hidden');
        wrapper.appendChild(select);
    }

    // ── live search (debounced auto-submit + clear button) ──
    function initLiveSearch(input) {
        if (input.dataset.lsDone) return;
        input.dataset.lsDone = '1';

        var form = input.closest('form');
        if (!form) return;

        var clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'ls-clear-btn';
        clearBtn.innerHTML = '&times;';
        clearBtn.title = 'Bersihkan pencarian';
        clearBtn.setAttribute('aria-label', 'Bersihkan pencarian');
        input.insertAdjacentElement('afterend', clearBtn);

        var timer = null;
        var lastValue = input.value;

        function submit() {
            form.submit(); // GET -> navigates with current query params
        }

        input.addEventListener('input', function () {
            clearBtn.classList.toggle('show', !!input.value);
            if (input.value === lastValue) return;
            lastValue = input.value;
            clearTimeout(timer);
            timer = setTimeout(submit, 450);
        });
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && input.value) {
                e.preventDefault();
                input.value = '';
                clearBtn.classList.remove('show');
                submit();
            }
        });
        clearBtn.addEventListener('click', function () {
            input.value = '';
            clearBtn.classList.remove('show');
            input.focus();
            submit();
        });
        // show clear if server-side pre-filled
        clearBtn.classList.toggle('show', !!input.value);
    }

    function init() {
        document.querySelectorAll('select[data-searchable]').forEach(initSearchable);
        document.querySelectorAll('input[data-live-search]').forEach(initLiveSearch);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
